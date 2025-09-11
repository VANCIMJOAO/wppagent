"""
🔒 H001 - Teste de Validação de Assinatura do Webhook
=====================================================

Testes para verificar se a correção H001 está funcionando corretamente.
"""

import pytest
import json
import hmac
import hashlib
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app.main import app


class TestH001WebhookSignature:
    """Testes para H001 - Validação de assinatura do webhook"""
    
    def setup_method(self):
        """Setup para cada teste"""
        self.client = TestClient(app)
        self.webhook_url = "/webhook"
        self.test_payload = {
            "entry": [
                {
                    "id": "123456789",
                    "changes": [
                        {
                            "value": {
                                "messaging_product": "whatsapp",
                                "metadata": {
                                    "display_phone_number": "5511999999999",
                                    "phone_number_id": "123456789"
                                },
                                "messages": [
                                    {
                                        "from": "5511888888888",
                                        "id": "wamid.123",
                                        "timestamp": "1640995200",
                                        "text": {"body": "Hello"},
                                        "type": "text"
                                    }
                                ]
                            },
                            "field": "messages"
                        }
                    ]
                }
            ]
        }
        self.webhook_secret = "test_webhook_secret_123"
        
    def generate_signature(self, payload: str, secret: str) -> str:
        """Gerar assinatura válida para teste"""
        signature = hmac.new(
            secret.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return f"sha256={signature}"
    
    @patch('app.services.whatsapp_security.WhatsAppSecurityService')
    def test_webhook_without_signature_should_fail(self, mock_security_service):
        """Teste: Webhook sem assinatura deve retornar 403"""
        # Configurar mock para falhar na validação
        mock_instance = MagicMock()
        mock_instance.validate_webhook_request.return_value = False
        mock_security_service.return_value = mock_instance
        
        # Enviar request sem assinatura
        response = self.client.post(
            self.webhook_url,
            json=self.test_payload,
            headers={"Content-Type": "application/json"}
        )
        
        # Verificar se retorna 403
        assert response.status_code == 403
        assert "signature validation failed" in response.json()["detail"].lower()
        
    @patch('app.services.whatsapp_security.WhatsAppSecurityService')
    def test_webhook_with_invalid_signature_should_fail(self, mock_security_service):
        """Teste: Webhook com assinatura inválida deve retornar 403"""
        # Configurar mock para falhar na validação
        mock_instance = MagicMock()
        mock_instance.validate_webhook_request.return_value = False
        mock_security_service.return_value = mock_instance
        
        # Enviar request com assinatura inválida
        response = self.client.post(
            self.webhook_url,
            json=self.test_payload,
            headers={
                "Content-Type": "application/json",
                "X-Hub-Signature-256": "sha256=invalid_signature"
            }
        )
        
        # Verificar se retorna 403
        assert response.status_code == 403
        assert "signature validation failed" in response.json()["detail"].lower()
        
    @patch('app.services.whatsapp_security.WhatsAppSecurityService')
    def test_webhook_with_valid_signature_should_pass(self, mock_security_service):
        """Teste: Webhook com assinatura válida deve passar"""
        # Configurar mock para passar na validação
        mock_instance = MagicMock()
        mock_instance.validate_webhook_request.return_value = True
        mock_security_service.return_value = mock_instance
        
        payload_str = json.dumps(self.test_payload)
        valid_signature = self.generate_signature(payload_str, self.webhook_secret)
        
        # Mock do banco de dados para evitar erros
        with patch('app.database.get_db') as mock_db:
            mock_session = MagicMock()
            mock_db.return_value = mock_session
            
            # Enviar request com assinatura válida
            response = self.client.post(
                self.webhook_url,
                json=self.test_payload,
                headers={
                    "Content-Type": "application/json",
                    "X-Hub-Signature-256": valid_signature
                }
            )
            
            # Verificar se não retorna 403 (deve processar normalmente)
            assert response.status_code != 403
            
    def test_h001_security_fix_implementation(self):
        """Teste: Verificar se a correção H001 foi implementada"""
        # Verificar se o import do WhatsAppSecurityService está presente
        from app.routes.webhook import security_service
        assert security_service is not None
        
        # Verificar se o método validate_webhook_request existe
        assert hasattr(security_service, 'validate_webhook_request')
        
    @patch('app.services.whatsapp_security.WhatsAppSecurityService')
    def test_security_logging_on_invalid_signature(self, mock_security_service):
        """Teste: Verificar se eventos de segurança são logados"""
        # Configurar mock para falhar na validação
        mock_instance = MagicMock()
        mock_instance.validate_webhook_request.return_value = False
        mock_security_service.return_value = mock_instance
        
        with patch('app.services.structured_apm.log_security_event') as mock_log_security:
            # Enviar request com assinatura inválida
            response = self.client.post(
                self.webhook_url,
                json=self.test_payload,
                headers={
                    "Content-Type": "application/json",
                    "X-Hub-Signature-256": "sha256=invalid_signature"
                }
            )
            
            # Verificar se evento de segurança foi logado
            assert response.status_code == 403
            mock_log_security.assert_called_once()
            
            # Verificar se foi logado como evento de assinatura inválida
            call_args = mock_log_security.call_args
            assert call_args[1]['event_type'] == "webhook_signature_invalid"
            assert call_args[1]['severity'] == "HIGH"
            
    def test_h001_fix_prevents_forged_requests(self):
        """Teste: H001 deve prevenir requisições forjadas"""
        # Este é o cenário de ataque descrito no H001
        forged_payload = {
            "entry": [
                {
                    "id": "malicious_id",
                    "changes": [
                        {
                            "value": {
                                "messages": [
                                    {
                                        "from": "attacker_number",
                                        "text": {"body": "malicious_message"},
                                        "type": "text"
                                    }
                                ]
                            },
                            "field": "messages"
                        }
                    ]
                }
            ]
        }
        
        # Tentar enviar POST forjado sem assinatura válida
        response = self.client.post(
            self.webhook_url,
            json=forged_payload,
            headers={"Content-Type": "application/json"}
        )
        
        # Deve ser rejeitado com 403
        assert response.status_code == 403
        assert "signature validation failed" in response.json()["detail"].lower()


if __name__ == "__main__":
    # Executar testes
    pytest.main([__file__, "-v"])
