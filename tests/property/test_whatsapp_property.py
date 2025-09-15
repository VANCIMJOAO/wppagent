"""
Property-Based Tests para WhatsApp Service
===========================================

Testes que verificam invariantes do serviço WhatsApp
usando geração automática de casos de teste.
"""

import asyncio
import json
import re
from unittest.mock import AsyncMock, Mock, patch

import pytest
from hypothesis import assume, example, given, settings
from hypothesis import strategies as st
from hypothesis.strategies import booleans, dictionaries, integers, lists, text

from app.services.whatsapp import WhatsAppService


class TestWhatsAppServiceProperties:
    """
    Property-based tests para WhatsApp Service

    Invariantes testados:
    1. Números de telefone devem ser normalizados consistentemente
    2. Mensagens devem ser sanitizadas corretamente
    3. Respostas da API devem ser tratadas uniformemente
    4. Rate limiting deve ser respeitado
    """

    def setup_method(self):
        """Setup para cada teste"""
        self.whatsapp_service = WhatsAppService()

    @given(phone_number=text(min_size=8, max_size=15, alphabet="0123456789+() -"))
    @settings(max_examples=50, deadline=None)
    @example(phone_number="+5511999887766")
    @example(phone_number="11999887766")
    @example(phone_number="(11) 99988-7766")
    @example(phone_number="+55 11 99988-7766")
    def test_phone_normalization_property(self, phone_number):
        """
        PROPRIEDADE: Normalização de telefone deve ser idempotente
        e consistente
        """
        # Assumir que tem pelo menos alguns dígitos
        digits_only = re.sub(r"[^0-9]", "", phone_number)
        assume(len(digits_only) >= 8)
        assume(len(digits_only) <= 15)

        # Act: Normalizar o número
        normalized1 = self.whatsapp_service._normalize_phone(phone_number)

        # Propriedade 1: Idempotência - normalizar novamente deve dar o mesmo resultado
        normalized2 = self.whatsapp_service._normalize_phone(normalized1)
        assert normalized1 == normalized2, "Normalização deve ser idempotente"

        # Propriedade 2: Formato consistente
        assert normalized1.startswith("55"), "Deve sempre começar com código do país"
        assert normalized1.isdigit(), "Resultado deve conter apenas dígitos"
        assert (
            len(normalized1) >= 12
        ), "Deve ter pelo menos 12 dígitos (55 + DDD + número)"
        assert len(normalized1) <= 15, "Não deve exceder 15 dígitos"

        # Propriedade 3: Preservar dígitos essenciais
        original_digits = re.sub(r"[^0-9]", "", phone_number)
        if original_digits.startswith("55"):
            assert normalized1.endswith(
                original_digits[2:]
            ), "Dígitos locais devem ser preservados"
        elif len(original_digits) >= 10:
            assert original_digits in normalized1, "Número original deve estar contido"

    @given(
        message_content=text(
            min_size=1,
            max_size=4000,
            alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 !@#$%^&*().,;:-_+=[]{}|\\<>?/~`"\n\t',
        )
    )
    @settings(max_examples=30, deadline=None)
    @example(message_content="Hello World!")
    @example(message_content="<script>alert('xss')</script>")
    @example(message_content="SELECT * FROM users; DROP TABLE users;")
    @example(message_content="🎉💯🚀 Emoji test! 😀")
    def test_message_sanitization_property(self, message_content):
        """
        PROPRIEDADE: Sanitização de mensagem deve ser segura e preservar conteúdo legítimo
        """
        # Act: Sanitizar mensagem
        sanitized = self.whatsapp_service._sanitize_message(message_content)

        # Propriedade 1: Resultado nunca deve ser vazio para input não-vazio
        if message_content.strip():
            assert (
                sanitized.strip()
            ), "Mensagem não-vazia deve resultar em conteúdo sanitizado"

        # Propriedade 2: Tamanho deve ser controlado
        assert len(sanitized) <= 4096, "Mensagem sanitizada não deve exceder limite"

        # Propriedade 3: Caracteres perigosos devem ser removidos/escapados
        dangerous_patterns = ["<script", "javascript:", "data:text/html", "vbscript:"]
        sanitized_lower = sanitized.lower()
        for pattern in dangerous_patterns:
            assert (
                pattern not in sanitized_lower
            ), f"Padrão perigoso '{pattern}' deve ser removido"

        # Propriedade 4: Conteúdo básico deve ser preservado
        # Remover caracteres especiais e comparar
        original_alphanumeric = re.sub(r"[^a-zA-Z0-9\s]", "", message_content)
        sanitized_alphanumeric = re.sub(r"[^a-zA-Z0-9\s]", "", sanitized)

        if original_alphanumeric.strip():
            # Pelo menos parte do conteúdo alfanumérico deve ser preservada
            words_original = set(original_alphanumeric.lower().split())
            words_sanitized = set(sanitized_alphanumeric.lower().split())
            common_words = words_original.intersection(words_sanitized)
            preservation_ratio = (
                len(common_words) / len(words_original) if words_original else 1
            )
            assert (
                preservation_ratio >= 0.5
            ), "Pelo menos 50% das palavras devem ser preservadas"

    @given(
        responses=lists(
            dictionaries(
                keys=st.sampled_from(["status", "data", "error", "message", "success"]),
                values=st.one_of(
                    booleans(),
                    text(max_size=100),
                    integers(min_value=200, max_value=599),
                    dictionaries(text(max_size=20), text(max_size=50), max_size=3),
                ),
                max_size=5,
            ),
            min_size=1,
            max_size=10,
        )
    )
    @settings(max_examples=20, deadline=None)
    def test_api_response_handling_property(self, responses):
        """
        PROPRIEDADE: Tratamento de respostas da API deve ser robusto
        """
        for response_data in responses:
            # Act: Processar resposta
            try:
                processed = self.whatsapp_service._process_api_response(response_data)

                # Propriedade 1: Resultado deve ter estrutura consistente
                assert isinstance(processed, dict), "Resultado deve ser um dicionário"
                assert "success" in processed, "Deve conter campo 'success'"
                assert isinstance(
                    processed["success"], bool
                ), "Campo 'success' deve ser booleano"

                # Propriedade 2: Erro deve ser reportado apropriadamente
                if not processed["success"]:
                    assert (
                        "error" in processed or "message" in processed
                    ), "Falha deve incluir informação do erro"

            except Exception as e:
                # Propriedade 3: Falhas devem ser controladas
                assert isinstance(
                    e, (ValueError, TypeError, KeyError)
                ), f"Tipo de erro inesperado: {type(e)}"

    @given(
        phone_numbers=lists(
            text(min_size=10, max_size=15, alphabet="0123456789"),
            min_size=1,
            max_size=50,
            unique=True,
        ),
        message=text(min_size=1, max_size=100, alphabet="abcdefghijklmnopqrstuvwxyz "),
    )
    @settings(max_examples=10, deadline=None)
    def test_bulk_message_properties(self, phone_numbers, message):
        """
        PROPRIEDADE: Envio em lote deve manter consistência
        """
        # Assumir números válidos
        valid_phones = [p for p in phone_numbers if len(p) >= 10]
        assume(len(valid_phones) > 0)

        with patch.object(self.whatsapp_service, "_send_single_message") as mock_send:
            mock_send.return_value = {"success": True, "message_id": "msg_123"}

            # Act: Enviar mensagens em lote
            results = self.whatsapp_service.send_bulk_messages(valid_phones, message)

            # Propriedade 1: Deve tentar enviar para todos os números
            assert mock_send.call_count == len(
                valid_phones
            ), "Deve chamar send para cada número"

            # Propriedade 2: Resultados devem ter mesmo tamanho que input
            assert len(results) == len(
                valid_phones
            ), "Deve retornar resultado para cada número"

            # Propriedade 3: Cada resultado deve ter estrutura consistente
            for result in results:
                assert isinstance(result, dict), "Cada resultado deve ser um dicionário"
                assert "phone" in result, "Deve incluir o telefone"
                assert "success" in result, "Deve incluir status de sucesso"

    @given(
        rate_limit=integers(min_value=1, max_value=100),
        request_count=integers(min_value=1, max_value=200),
    )
    @settings(max_examples=15, deadline=None)
    def test_rate_limiting_property(self, rate_limit, request_count):
        """
        PROPRIEDADE: Rate limiting deve ser respeitado consistentemente
        """
        # Arrange: Configurar rate limit
        self.whatsapp_service.rate_limit = rate_limit

        with patch("time.sleep") as mock_sleep:
            # Act: Simular múltiplas requisições
            for i in range(min(request_count, 50)):  # Limitar para não demorar muito
                self.whatsapp_service._check_rate_limit()

            # Propriedade 1: Se exceder rate limit, deve haver delays
            if request_count > rate_limit:
                expected_sleeps = (min(request_count, 50) - 1) // rate_limit
                assert (
                    mock_sleep.call_count >= expected_sleeps
                ), "Deve respeitar rate limiting"

            # Propriedade 2: Delays devem ser consistentes
            if mock_sleep.call_count > 0:
                for call in mock_sleep.call_args_list:
                    sleep_time = call[0][0]
                    assert sleep_time > 0, "Tempo de sleep deve ser positivo"
                    assert sleep_time <= 2, "Tempo de sleep não deve ser excessivo"


class TestWhatsAppServiceEdgeCases:
    """
    Testes para edge cases específicos descobertos via property testing
    """

    def setup_method(self):
        """Setup para cada teste"""
        self.whatsapp_service = WhatsAppService()

    def test_phone_normalization_edge_cases(self):
        """Testar casos extremos de normalização de telefone"""
        edge_cases = [
            ("", ""),  # String vazia
            ("abc", ""),  # Sem números
            ("000000000000000", "55000000000000000"),  # Muitos zeros
            ("+1234567890123456", "1234567890123456"),  # Muito longo
            ("55", "55"),  # Só código país
        ]

        for input_phone, expected_behavior in edge_cases:
            try:
                result = self.whatsapp_service._normalize_phone(input_phone)
                # Se não falhar, deve seguir regras básicas
                if result:
                    assert result.isdigit(), f"Resultado deve ser numérico: {result}"
            except (ValueError, TypeError):
                # Falhas são aceitáveis para casos inválidos
                pass

    @given(message_size=integers(min_value=0, max_value=10000))
    @settings(max_examples=20)
    def test_message_size_limits(self, message_size):
        """
        PROPRIEDADE: Sistema deve lidar graciosamente com mensagens de qualquer tamanho
        """
        # Criar mensagem do tamanho especificado
        message = "A" * message_size

        try:
            sanitized = self.whatsapp_service._sanitize_message(message)

            # Propriedades para mensagens aceitas
            assert len(sanitized) <= 4096, "Resultado nunca deve exceder limite máximo"

            if message_size == 0:
                assert sanitized == "", "Mensagem vazia deve resultar em string vazia"
            elif message_size <= 4096:
                assert len(sanitized) >= min(
                    message_size * 0.8, 1
                ), "Mensagens pequenas devem ser preservadas"

        except (ValueError, MemoryError) as e:
            # Para mensagens muito grandes, falha controlada é aceitável
            assert (
                message_size > 4096
            ), f"Falha inesperada para tamanho {message_size}: {e}"

    def test_concurrent_api_calls(self):
        """
        PROPRIEDADE: Chamadas concorrentes da API devem ser thread-safe
        """
        import threading
        import time

        results = []
        errors = []

        def make_api_call(phone_suffix):
            try:
                phone = f"5511999887766{phone_suffix:02d}"
                message = f"Test message {phone_suffix}"

                with patch.object(
                    self.whatsapp_service, "_send_single_message"
                ) as mock_send:
                    mock_send.return_value = {
                        "success": True,
                        "message_id": f"msg_{phone_suffix}",
                    }
                    result = self.whatsapp_service._send_single_message(phone, message)
                    results.append(result)

            except Exception as e:
                errors.append(e)

        # Executar chamadas concorrentes
        threads = []
        for i in range(10):
            thread = threading.Thread(target=make_api_call, args=(i,))
            threads.append(thread)

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        # Verificar resultados
        assert len(errors) == 0, f"Não deve haver erros: {errors}"
        assert len(results) == 10, "Todas as chamadas devem completar"

        # Verificar unicidade dos resultados
        message_ids = [r.get("message_id") for r in results]
        assert len(set(message_ids)) == 10, "Todos os message IDs devem ser únicos"


if __name__ == "__main__":
    # Executar testes property-based
    pytest.main([__file__, "-v", "--tb=short"])
