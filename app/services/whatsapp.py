"""
Serviço para integração com WhatsApp Cloud API COM RETRY ROBUSTO
"""
import json
import httpx
from typing import Dict, List, Optional, Any
from app.config import settings
from app.utils.logger import get_logger
from app.models.database import MetaLog
logger = get_logger(__name__)
from app.database import AsyncSessionLocal
from app.services.retry_handler import retry_handler, CircuitBreakerConfig
from app.services.whatsapp_security import whatsapp_security
import logging

logger = logging.getLogger(__name__)


class WhatsAppService:
    """Serviço para interação com WhatsApp Cloud API com retry robusto"""
    
    def __init__(self):
        self.base_url = settings.whatsapp_api_url
        self.phone_number_id = settings.whatsapp_phone_id
        self.access_token = settings.whatsapp_token.get_secret_value() if settings.whatsapp_token else None
        
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        # Configuração do circuit breaker para WhatsApp API
        self.circuit_breaker_config = CircuitBreakerConfig(
            failure_threshold=3,
            recovery_timeout=300,  # 5 minutos - tempo realista para recuperação da API
            expected_exception=Exception
        )
    
    async def _log_request(self, method: str, endpoint: str, payload: Dict = None, 
                          response: Dict = None, status_code: int = None):
        """Registra logs das requisições para a Meta API"""
        try:
            async with AsyncSessionLocal() as session:
                log_entry = MetaLog(
                    direction="out",
                    endpoint=endpoint,
                    method=method,
                    status_code=status_code,
                    headers=self.headers,
                    payload=payload,
                    response=response
                )
                session.add(log_entry)
                await session.commit()
        except Exception as e:
            logger.error(f"Erro ao salvar log: {e}")
    
    async def _make_api_request(self, endpoint: str, payload: Dict) -> Dict:
        """Faz requisição para a API com tratamento de erros"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                endpoint, 
                headers=self.headers, 
                json=payload,
                timeout=30.0
            )
            
            response_data = response.json()
            
            await self._log_request(
                method="POST",
                endpoint=endpoint,
                payload=payload,
                response=response_data,
                status_code=response.status_code
            )
            
            # Verificar se houve erro de autenticação ou rate limiting
            if response.status_code == 401:
                raise Exception(f"Token inválido ou expirado: {response_data}")
            elif response.status_code == 429:
                raise Exception(f"Rate limit excedido: {response_data}")
            elif response.status_code >= 400:
                raise Exception(f"Erro na API ({response.status_code}): {response_data}")
            
            return response_data
    
    async def send_text_message(self, to: str, message: str) -> Dict:
        """
        Envia mensagem de texto com retry robusto e fallback
        
        Args:
            to: Número do destinatário (wa_id)
            message: Texto da mensagem
        """
        try:
            # Usar o novo serviço de segurança com retry robusto
            result = await whatsapp_security.send_message(
                phone_number=to,
                message=message,
                message_type="text"
            )
            
            if result:
                logger.info(f"✅ Mensagem enviada para {to}")
                return result
            else:
                logger.warning(f"⚠️ Mensagem para {to} adicionada à fila de fallback")
                return {"status": "queued", "message": "Mensagem na fila de fallback"}
            
        except Exception as e:
            logger.error(f"❌ Falha ao enviar mensagem para {to}: {e}")
            return {"error": str(e)}
    
    async def send_interactive_buttons(self, to: str, text: str, buttons: List[Dict]) -> Dict:
        """
        Envia mensagem com botões interativos com retry automático
        
        Args:
            to: Número do destinatário
            text: Texto da mensagem
            buttons: Lista de botões [{"id": "btn_1", "title": "Confirmar"}]
        """
        endpoint = f"{self.base_url}/{self.phone_number_id}/messages"
        
        # Formatar botões para a API
        formatted_buttons = []
        for i, btn in enumerate(buttons):
            formatted_buttons.append({
                "type": "reply",
                "reply": {
                    "id": btn.get("id", f"btn_{i}"),
                    "title": btn.get("title", f"Opção {i+1}")
                }
            })
        
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "body": {
                    "text": text
                },
                "action": {
                    "buttons": formatted_buttons
                }
            }
        }
        
        try:
            result = await retry_handler.execute_with_retry(
                func=self._make_api_request,
                service_name="whatsapp_api",
                max_retries=3,
                base_delay=2.0,
                circuit_breaker_config=self.circuit_breaker_config,
                endpoint=endpoint,
                payload=payload
            )
            
            logger.info(f"Botões interativos enviados para {to}")
            return result
            
        except Exception as e:
            logger.error(f"Falha definitiva ao enviar botões para {to}: {e}")
            return {"error": str(e)}
    
    async def download_media(self, media_id: str) -> Optional[bytes]:
        """
        Baixa mídia (áudio, imagem, etc.) do WhatsApp
        
        Args:
            media_id: ID da mídia no WhatsApp
            
        Returns:
            Bytes do arquivo ou None se erro
        """
        # Primeiro, obter a URL da mídia
        endpoint = f"{self.base_url}/{media_id}"
        
        async with httpx.AsyncClient() as client:
            try:
                # Obter URL da mídia
                response = await client.get(
                    endpoint, 
                    headers=self.headers,
                    timeout=30.0  # Timeout adequado para download de mídia
                )
                
                if response.status_code == 200:
                    media_data = response.json()
                    media_url = media_data.get("url")
                    
                    if not media_url:
                        return None
                    
                    # Baixar o arquivo
                    media_response = await client.get(
                        media_url, 
                        headers={"Authorization": f"Bearer {self.access_token}"},
                        timeout=60.0  # Timeout maior para download de arquivo
                    )
                    
                    if media_response.status_code == 200:
                        return media_response.content
                    
                return None
            except Exception as e:
                logger.error(f"Erro ao baixar mídia {media_id}: {e}")
                return None
    
    def verify_webhook(self, verify_token: str, challenge: str) -> Optional[str]:
        """
        Verifica webhook do WhatsApp
        
        Args:
            verify_token: Token de verificação recebido
            challenge: Challenge recebido
            
        Returns:
            Challenge se verificação OK, None caso contrário
        """
        try:
            # Debug: verificar se o token está sendo carregado corretamente
            from app.config.config_factory import get_settings
            config = get_settings()
            logger.info(f"Config type: {type(config)}")
            logger.info(f"Config webhook_verify_token: {config.webhook_verify_token}")
            logger.info(f"Config webhook_verify_token type: {type(config.webhook_verify_token)}")
            
            if config.webhook_verify_token:
                expected_token_value = config.webhook_verify_token.get_secret_value()
                logger.info(f"Expected token value: '{expected_token_value}'")
            else:
                logger.info("webhook_verify_token is None")
                expected_token_value = None
            
            # Usar o valor real para comparação
            expected_token = settings.webhook_verify_token
            logger.info(f"Comparando tokens: recebido='{verify_token}', esperado='{expected_token}'")
            logger.info(f"Expected token real value: '{expected_token_value}'")
            
            if verify_token == expected_token_value:
                logger.info("✅ Tokens coincidem!")
                return challenge
            else:
                logger.info("❌ Tokens NÃO coincidem!")
        except Exception as e:
            logger.error(f"Erro ao acessar webhook_verify_token: {e}")
        return None


# Instância global do serviço
whatsapp_service = WhatsAppService()
