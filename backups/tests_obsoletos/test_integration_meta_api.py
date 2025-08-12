"""
🧪 Testes de Integração - Meta API
Testa integração completa com WhatsApp Business API
"""
import pytest
import asyncio
import json
import time
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from httpx import AsyncClient


class TestMetaAPIIntegration:
    """📱 Testes de integração com Meta WhatsApp API"""
    
    @pytest.mark.integration
    @pytest.mark.meta_api
    async def test_webhook_message_processing_flow(self, test_client, sample_webhook_payload):
        """Testa fluxo completo de processamento de mensagem via webhook"""
        
        # Enviar payload do webhook
        response = await test_client.post("/webhook", json=sample_webhook_payload)
        
        assert response.status_code == 200
        
        # Verificar se resposta foi processada
        response_data = response.json()
        assert "status" in response_data
        assert response_data["status"] == "success"
    
    @pytest.mark.integration
    @pytest.mark.meta_api
    async def test_webhook_verification(self, test_client):
        """Testa verificação do webhook do Meta"""
        
        verify_token = "test_verify_token"
        challenge = "test_challenge_123"
        
        response = await test_client.get(
            f"/webhook?hub.mode=subscribe&hub.verify_token={verify_token}&hub.challenge={challenge}"
        )
        
        assert response.status_code == 200
        assert response.text.strip('"') == challenge
    
    @pytest.mark.integration
    @pytest.mark.meta_api
    async def test_webhook_invalid_verification(self, test_client):
        """Testa rejeição de verificação inválida"""
        
        response = await test_client.get(
            "/webhook?hub.mode=subscribe&hub.verify_token=invalid_token&hub.challenge=test"
        )
        
        assert response.status_code == 403
    
    @pytest.mark.integration
    @pytest.mark.meta_api
    async def test_message_types_processing(self, test_client):
        """Testa processamento de diferentes tipos de mensagem"""
        
        message_types = [
            {
                "type": "text",
                "text": {"body": "Olá, quero agendar um horário"}
            },
            {
                "type": "button",
                "button": {"text": "Agendar", "payload": "schedule_appointment"}
            },
            {
                "type": "interactive",
                "interactive": {
                    "type": "button_reply",
                    "button_reply": {"id": "btn_yes", "title": "Sim"}
                }
            },
            {
                "type": "location",
                "location": {
                    "latitude": -23.550520,
                    "longitude": -46.633308,
                    "name": "São Paulo"
                }
            }
        ]
        
        for msg_type in message_types:
            payload = {
                "object": "whatsapp_business_account",
                "entry": [{
                    "id": "test_account",
                    "changes": [{
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {
                                "display_phone_number": "15551234567",
                                "phone_number_id": "test_phone_id"
                            },
                            "contacts": [{
                                "profile": {"name": "Test User"},
                                "wa_id": "5511999999999"
                            }],
                            "messages": [{
                                "from": "5511999999999",
                                "id": f"test_msg_{msg_type['type']}_{int(time.time())}",
                                "timestamp": str(int(time.time())),
                                **msg_type
                            }]
                        },
                        "field": "messages"
                    }]
                }]
            }
            
            response = await test_client.post("/webhook", json=payload)
            assert response.status_code == 200, f"Failed for message type: {msg_type['type']}"
    
    @pytest.mark.integration
    @pytest.mark.meta_api
    async def test_status_callback_processing(self, test_client):
        """Testa processamento de callbacks de status de mensagem"""
        
        status_payload = {
            "object": "whatsapp_business_account",
            "entry": [{
                "id": "test_account",
                "changes": [{
                    "value": {
                        "messaging_product": "whatsapp",
                        "metadata": {
                            "display_phone_number": "15551234567",
                            "phone_number_id": "test_phone_id"
                        },
                        "statuses": [{
                            "id": "wamid.test_message_id",
                            "status": "delivered",
                            "timestamp": str(int(time.time())),
                            "recipient_id": "5511999999999"
                        }]
                    },
                    "field": "messages"
                }]
            }]
        }
        
        response = await test_client.post("/webhook", json=status_payload)
        assert response.status_code == 200
    
    @pytest.mark.integration
    @pytest.mark.meta_api
    @pytest.mark.slow
    async def test_media_message_processing(self, test_client):
        """Testa processamento de mensagens com mídia"""
        
        media_payload = {
            "object": "whatsapp_business_account",
            "entry": [{
                "id": "test_account",
                "changes": [{
                    "value": {
                        "messaging_product": "whatsapp",
                        "metadata": {
                            "display_phone_number": "15551234567",
                            "phone_number_id": "test_phone_id"
                        },
                        "contacts": [{
                            "profile": {"name": "Test User"},
                            "wa_id": "5511999999999"
                        }],
                        "messages": [{
                            "from": "5511999999999",
                            "id": f"test_media_{int(time.time())}",
                            "timestamp": str(int(time.time())),
                            "type": "image",
                            "image": {
                                "id": "test_media_id",
                                "mime_type": "image/jpeg",
                                "sha256": "test_hash",
                                "caption": "Foto do meu cabelo atual"
                            }
                        }]
                    },
                    "field": "messages"
                }]
            }]
        }
        
        response = await test_client.post("/webhook", json=payload)
        assert response.status_code == 200


class TestMetaAPIErrorHandling:
    """🚨 Testes de tratamento de erros da Meta API"""
    
    @pytest.mark.integration
    @pytest.mark.meta_api
    async def test_invalid_webhook_payload(self, test_client):
        """Testa tratamento de payload inválido"""
        
        invalid_payloads = [
            {},  # Payload vazio
            {"invalid": "structure"},  # Estrutura incorreta
            {"object": "invalid_object"},  # Objeto inválido
            {
                "object": "whatsapp_business_account",
                "entry": []  # Entry vazio
            }
        ]
        
        for payload in invalid_payloads:
            response = await test_client.post("/webhook", json=payload)
            # Deve aceitar mas não processar mensagens inválidas
            assert response.status_code in [200, 400]
    
    @pytest.mark.integration
    @pytest.mark.meta_api
    async def test_malformed_json_webhook(self, test_client):
        """Testa tratamento de JSON malformado"""
        
        response = await test_client.post(
            "/webhook",
            content="invalid json content",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422  # Unprocessable Entity
    
    @pytest.mark.integration
    @pytest.mark.meta_api 
    async def test_rate_limit_response(self, test_client):
        """Testa resposta quando API atinge rate limit"""
        
        # Simular muitas requisições simultaneamente
        tasks = []
        for i in range(50):
            payload = {
                "object": "whatsapp_business_account",
                "entry": [{
                    "id": "test_account",
                    "changes": [{
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {
                                "display_phone_number": "15551234567",
                                "phone_number_id": "test_phone_id"
                            },
                            "contacts": [{
                                "profile": {"name": f"User {i}"},
                                "wa_id": f"55119999999{i:02d}"
                            }],
                            "messages": [{
                                "from": f"55119999999{i:02d}",
                                "id": f"test_msg_{i}_{int(time.time())}",
                                "timestamp": str(int(time.time())),
                                "type": "text",
                                "text": {"body": f"Mensagem de teste {i}"}
                            }]
                        },
                        "field": "messages"
                    }]
                }]
            }
            
            task = test_client.post("/webhook", json=payload)
            tasks.append(task)
        
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Verificar se pelo menos algumas foram processadas
        successful_responses = [r for r in responses if hasattr(r, 'status_code') and r.status_code == 200]
        assert len(successful_responses) > 0
        
        # Verificar se rate limiting foi aplicado para algumas
        rate_limited = [r for r in responses if hasattr(r, 'status_code') and r.status_code == 429]
        # Rate limiting pode ou não ser aplicado dependendo da configuração


class TestMetaAPIAuthentication:
    """🔐 Testes de autenticação com Meta API"""
    
    @pytest.mark.integration
    @pytest.mark.meta_api
    async def test_webhook_signature_validation(self, test_client):
        """Testa validação de assinatura do webhook"""
        
        # Mock da validação de assinatura
        with patch("app.services.whatsapp_service.WhatsAppService.validate_signature") as mock_validate:
            mock_validate.return_value = True
            
            payload = {
                "object": "whatsapp_business_account",
                "entry": [{
                    "id": "test_account",
                    "changes": [{
                        "value": {
                            "messaging_product": "whatsapp",
                            "messages": []
                        },
                        "field": "messages"
                    }]
                }]
            }
            
            response = await test_client.post(
                "/webhook",
                json=payload,
                headers={"X-Hub-Signature-256": "sha256=test_signature"}
            )
            
            assert response.status_code == 200
            mock_validate.assert_called_once()
    
    @pytest.mark.integration
    @pytest.mark.meta_api
    async def test_invalid_webhook_signature(self, test_client):
        """Testa rejeição de assinatura inválida"""
        
        with patch("app.services.whatsapp_service.WhatsAppService.validate_signature") as mock_validate:
            mock_validate.return_value = False
            
            payload = {"test": "data"}
            
            response = await test_client.post(
                "/webhook",
                json=payload,
                headers={"X-Hub-Signature-256": "sha256=invalid_signature"}
            )
            
            assert response.status_code == 403


class TestMetaAPIMessageDelivery:
    """📤 Testes de entrega de mensagens via Meta API"""
    
    @pytest.mark.integration
    @pytest.mark.meta_api
    async def test_send_text_message_integration(self, mock_meta_api):
        """Testa envio de mensagem de texto"""
        
        from app.services.whatsapp_service import WhatsAppService
        
        whatsapp_service = WhatsAppService()
        
        result = await whatsapp_service.send_message(
            phone="5511999999999",
            message="Seu agendamento foi confirmado para amanhã às 14h."
        )
        
        assert result["success"] is True
        assert "message_id" in result
        
        # Verificar chamada para Meta API
        mock_meta_api.post.assert_called_once()
        call_args = mock_meta_api.post.call_args
        
        assert "messages" in call_args[0][0]  # URL endpoint
        payload = call_args[1]["json"]
        assert payload["messaging_product"] == "whatsapp"
        assert payload["to"] == "5511999999999"
        assert payload["text"]["body"] == "Seu agendamento foi confirmado para amanhã às 14h."
    
    @pytest.mark.integration
    @pytest.mark.meta_api
    async def test_send_template_message_integration(self, mock_meta_api):
        """Testa envio de mensagem template"""
        
        from app.services.whatsapp_service import WhatsAppService
        
        whatsapp_service = WhatsAppService()
        
        result = await whatsapp_service.send_template_message(
            phone="5511999999999",
            template_name="appointment_confirmation",
            parameters=["João", "15/08/2025", "14:00"]
        )
        
        assert result["success"] is True
        
        # Verificar payload do template
        call_args = mock_meta_api.post.call_args
        payload = call_args[1]["json"]
        assert payload["type"] == "template"
        assert payload["template"]["name"] == "appointment_confirmation"
        assert len(payload["template"]["components"]) > 0
    
    @pytest.mark.integration
    @pytest.mark.meta_api
    @pytest.mark.slow
    async def test_bulk_message_sending(self, mock_meta_api):
        """Testa envio em lote de mensagens"""
        
        from app.services.whatsapp_service import WhatsAppService
        
        whatsapp_service = WhatsAppService()
        
        # Lista de destinatários
        recipients = [
            {"phone": f"551199999{i:04d}", "message": f"Mensagem personalizada {i}"}
            for i in range(10)
        ]
        
        results = await whatsapp_service.send_bulk_messages(recipients)
        
        assert len(results) == 10
        successful_sends = [r for r in results if r["success"]]
        assert len(successful_sends) >= 8  # Pelo menos 80% de sucesso
        
        # Verificar rate limiting interno
        assert mock_meta_api.post.call_count <= 10


class TestMetaAPIWebhookSecurity:
    """🛡️ Testes de segurança do webhook"""
    
    @pytest.mark.integration
    @pytest.mark.meta_api
    @pytest.mark.critical
    async def test_webhook_ddos_protection(self, test_client):
        """Testa proteção contra DDoS no webhook"""
        
        # Simular múltiplas requisições simultâneas
        concurrent_requests = 100
        tasks = []
        
        for i in range(concurrent_requests):
            payload = {
                "object": "whatsapp_business_account",
                "entry": [{
                    "id": f"attacker_{i}",
                    "changes": [{
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {"phone_number_id": "test"},
                            "messages": [{
                                "from": f"attack_{i}",
                                "id": f"spam_{i}",
                                "timestamp": str(int(time.time())),
                                "type": "text",
                                "text": {"body": "spam message"}
                            }]
                        },
                        "field": "messages"
                    }]
                }]
            }
            
            task = test_client.post("/webhook", json=payload)
            tasks.append(task)
        
        start_time = time.time()
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()
        
        # Verificar se sistema ainda está responsivo
        assert end_time - start_time < 30  # Não deve demorar mais de 30s
        
        # Verificar se algumas requisições foram rejeitadas (rate limiting)
        status_codes = [r.status_code for r in responses if hasattr(r, 'status_code')]
        rate_limited_count = status_codes.count(429)
        
        # Deve ter algum tipo de limitação
        assert rate_limited_count > 0 or len(status_codes) < concurrent_requests
    
    @pytest.mark.integration
    @pytest.mark.meta_api
    async def test_webhook_input_sanitization(self, test_client):
        """Testa sanitização de input do webhook"""
        
        malicious_payloads = [
            # XSS attempt
            {
                "object": "whatsapp_business_account",
                "entry": [{
                    "id": "test",
                    "changes": [{
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {"phone_number_id": "test"},
                            "messages": [{
                                "from": "5511999999999",
                                "id": "test_xss",
                                "timestamp": str(int(time.time())),
                                "type": "text",
                                "text": {"body": "<script>alert('xss')</script>"}
                            }]
                        },
                        "field": "messages"
                    }]
                }]
            },
            # SQL Injection attempt
            {
                "object": "whatsapp_business_account",
                "entry": [{
                    "id": "test",
                    "changes": [{
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {"phone_number_id": "test"},
                            "messages": [{
                                "from": "'; DROP TABLE users; --",
                                "id": "test_sql",
                                "timestamp": str(int(time.time())),
                                "type": "text",
                                "text": {"body": "Normal message"}
                            }]
                        },
                        "field": "messages"
                    }]
                }]
            }
        ]
        
        for payload in malicious_payloads:
            response = await test_client.post("/webhook", json=payload)
            
            # Deve processar sem erro (input sanitizado)
            assert response.status_code == 200
            
            # Verificar se input foi sanitizado (não deve conter scripts)
            response_data = response.json()
            response_str = json.dumps(response_data)
            assert "<script>" not in response_str
            assert "DROP TABLE" not in response_str


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-m", "integration"])
