"""
🛡️ Serviço de Segurança WhatsApp
===============================

Implementa:
- Validação de assinatura do webhook
- Retry logic robusto para Meta API
- Handling para rate limits da Meta
- Fallback para indisponibilidade da API
"""

import asyncio
import hashlib
import hmac
import json
import logging
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, Request

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)
from enum import Enum

import aiohttp

logger = logging.getLogger(__name__)


class MetaAPIStatus(Enum):
    """Status da Meta API"""

    AVAILABLE = "available"
    RATE_LIMITED = "rate_limited"
    UNAVAILABLE = "unavailable"
    DEGRADED = "degraded"


class WhatsAppSecurityService:
    """Serviço de segurança para WhatsApp"""

    def __init__(self):
        # Obter webhook_secret garantindo que seja uma string
        webhook_secret_raw = settings.whatsapp_webhook_secret
        if webhook_secret_raw and hasattr(webhook_secret_raw, "get_secret_value"):
            self.webhook_secret = webhook_secret_raw.get_secret_value()
        else:
            self.webhook_secret = webhook_secret_raw

        self.access_token = getattr(settings, "meta_access_token", None)
        if self.access_token and hasattr(self.access_token, "get_secret_value"):
            self.access_token = self.access_token.get_secret_value()
        self.phone_number_id = getattr(settings, "whatsapp_phone_id", None)
        self.api_base_url = "https://graph.facebook.com/v18.0"

        # Rate limiting tracking
        self.rate_limit_reset_time: Optional[datetime] = None
        self.requests_remaining: int = 1000  # Default limit
        self.api_status = MetaAPIStatus.AVAILABLE

        # Retry configuration
        self.max_retries = 3
        self.base_delay = 1.0
        self.max_delay = 60.0

        # Fallback queue para quando API estiver indisponível
        self.fallback_queue: List[Dict[str, Any]] = []

    def validate_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """
        HF001 FIX: Validação obrigatória de assinatura HMAC SHA256

        Args:
            payload: Payload bruto do webhook
            signature: Assinatura do header X-Hub-Signature-256

        Returns:
            bool: True se assinatura for válida
        """
        # HF001 FIX: Webhook secret é OBRIGATÓRIO - sem bypass
        if not self.webhook_secret:
            logger.error(
                "� HF001 PROTECTION: WHATSAPP_WEBHOOK_SECRET não configurado - webhook rejeitado"
            )
            return False

        if not signature:
            logger.error(
                "🔒 HF001 PROTECTION: Assinatura do webhook não fornecida - webhook rejeitado"
            )
            return False

        try:
            # Remove o prefixo 'sha256=' se presente
            original_signature = signature
            if signature.startswith("sha256="):
                signature = signature[7:]

            logger.info(f"� HF001 VALIDATION - Signature validation:")
            logger.info(f"  - Original signature: {original_signature[:20]}...")
            logger.info(f"  - Cleaned signature: {signature[:20]}...")
            logger.info(f"  - Payload length: {len(payload)}")

            # Calcula HMAC SHA256
            expected_signature = hmac.new(
                self.webhook_secret.encode("utf-8"), payload, hashlib.sha256
            ).hexdigest()

            # Comparação segura contra timing attacks
            is_valid = hmac.compare_digest(signature, expected_signature)

            if is_valid:
                logger.info(
                    "✅ HF001 PROTECTION: Webhook signature validation successful"
                )
            else:
                logger.error("🔒 HF001 PROTECTION: Webhook signature validation FAILED")
                logger.error(f"   Received: {signature}")
                logger.error(f"   Expected: {expected_signature}")

            return is_valid

        except Exception as e:
            logger.error(f"🔒 HF001 PROTECTION: Error in signature validation: {e}")
            return False

    async def validate_webhook_request(self, request: Request) -> bool:
        """
        HF001 FIX: Validação completa de requisição webhook com logs de segurança

        Args:
            request: Requisição FastAPI

        Returns:
            bool: True se requisição for válida
        """
        try:
            # Obter payload e assinatura
            payload = await request.body()
            signature = request.headers.get("X-Hub-Signature-256", "")

            # HF001 PROTECTION: Logs de segurança
            source_ip = request.client.host if request.client else "unknown"
            user_agent = request.headers.get("user-agent", "")
            content_type = request.headers.get("Content-Type", "")

            # Validar assinatura HMAC
            if not self.validate_webhook_signature(payload, signature):
                # Log de tentativa de acesso não autorizada
                logger.error(
                    f"🔒 HF001 SECURITY ALERT: Webhook with invalid signature rejected"
                )
                logger.error(f"  - Source IP: {source_ip}")
                logger.error(f"  - User-Agent: {user_agent}")
                logger.error(f"  - Content-Type: {content_type}")
                logger.error(f"  - Signature provided: {bool(signature)}")
                return False

            # Validações adicionais de segurança
            if content_type != "application/json":
                logger.warning(
                    f"🔒 HF001 WARNING: Unexpected content-type: {content_type}"
                )

            logger.info(
                f"✅ HF001 PROTECTION: Webhook request validated successfully from {source_ip}"
            )
            return True

        except Exception as e:
            logger.error(
                f"🔒 HF001 PROTECTION: Error in webhook request validation: {e}"
            )
            return False
            if "application/json" not in content_type:
                logger.error(f"❌ Content-Type inválido: {content_type}")
                return False

            # Verificar User-Agent do WhatsApp
            user_agent = request.headers.get("User-Agent", "")
            if not self._is_valid_whatsapp_user_agent(user_agent):
                logger.warning(f"🔶 User-Agent suspeito: {user_agent}")

            return True

        except Exception as e:
            logger.error(f"❌ Erro na validação da requisição webhook: {e}")
            return False

    def _is_valid_whatsapp_user_agent(self, user_agent: str) -> bool:
        """Verifica se o User-Agent é válido do WhatsApp"""
        valid_patterns = [r"WhatsApp", r"facebookexternalua", r"Meta", r"facebook"]

        for pattern in valid_patterns:
            if pattern.lower() in user_agent.lower():
                return True

        return False

    async def make_api_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Faz requisição para Meta API com retry logic e rate limiting

        Args:
            method: Método HTTP (GET, POST, etc.)
            endpoint: Endpoint da API (ex: "/messages")
            data: Dados para enviar
            params: Parâmetros da query

        Returns:
            Resposta da API ou None se falhar
        """
        url = f"{self.api_base_url}{endpoint}"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

        # Verificar rate limiting
        if self._is_rate_limited():
            logger.warning("⏰ Rate limit ativo - aguardando reset")
            await self._wait_for_rate_limit_reset()

        # Verificar status da API
        if self.api_status == MetaAPIStatus.UNAVAILABLE:
            logger.error("❌ Meta API indisponível - adicionando à fila de fallback")
            self._add_to_fallback_queue(method, endpoint, data, params)
            return None

        # Retry logic
        for attempt in range(self.max_retries + 1):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.request(
                        method=method,
                        url=url,
                        headers=headers,
                        json=data,
                        params=params,
                        timeout=aiohttp.ClientTimeout(total=30),
                    ) as response:

                        # Atualizar informações de rate limiting
                        self._update_rate_limit_info(response.headers)

                        if response.status == 200:
                            self.api_status = MetaAPIStatus.AVAILABLE
                            result = await response.json()
                            logger.info(
                                f"✅ API request successful: {method} {endpoint}"
                            )
                            return result

                        elif response.status == 429:  # Rate limited
                            self._handle_rate_limit(response.headers)
                            if attempt < self.max_retries:
                                delay = self._calculate_retry_delay(attempt)
                                logger.warning(
                                    f"⏰ Rate limited - retry {attempt + 1}/{self.max_retries} em {delay}s"
                                )
                                await asyncio.sleep(delay)
                                continue

                        elif response.status in [500, 502, 503, 504]:  # Server errors
                            self.api_status = MetaAPIStatus.DEGRADED
                            if attempt < self.max_retries:
                                delay = self._calculate_retry_delay(attempt)
                                logger.warning(
                                    f"🔶 Server error {response.status} - retry {attempt + 1}/{self.max_retries} em {delay}s"
                                )
                                await asyncio.sleep(delay)
                                continue

                        else:
                            error_text = await response.text()
                            logger.error(
                                f"❌ API request failed: {response.status} - {error_text}"
                            )
                            break

            except asyncio.TimeoutError:
                logger.error(
                    f"⏰ Timeout na requisição - attempt {attempt + 1}/{self.max_retries + 1}"
                )
                if attempt < self.max_retries:
                    delay = self._calculate_retry_delay(attempt)
                    await asyncio.sleep(delay)
                    continue

            except Exception as e:
                logger.error(
                    f"❌ Erro na requisição API: {e} - attempt {attempt + 1}/{self.max_retries + 1}"
                )
                if attempt < self.max_retries:
                    delay = self._calculate_retry_delay(attempt)
                    await asyncio.sleep(delay)
                    continue

        # Se chegou aqui, todas as tentativas falharam
        logger.error(f"❌ Todas as tentativas falharam para {method} {endpoint}")
        self.api_status = MetaAPIStatus.UNAVAILABLE
        self._add_to_fallback_queue(method, endpoint, data, params)
        return None

    def _is_rate_limited(self) -> bool:
        """Verifica se estamos em rate limit"""
        if self.rate_limit_reset_time:
            return datetime.now(timezone.utc) < self.rate_limit_reset_time
        return False

    async def _wait_for_rate_limit_reset(self):
        """Aguarda o reset do rate limit"""
        if self.rate_limit_reset_time:
            wait_time = (
                self.rate_limit_reset_time - datetime.now(timezone.utc)
            ).total_seconds()
            if wait_time > 0:
                logger.info(f"⏰ Aguardando {wait_time:.1f}s para reset do rate limit")
                await asyncio.sleep(min(wait_time, 60))  # Máximo 1 minuto

    def _update_rate_limit_info(self, headers: Dict[str, str]):
        """Atualiza informações de rate limiting dos headers da resposta"""
        try:
            # Headers do WhatsApp Business API
            if "X-Business-Use-Case-Usage" in headers:
                usage_info = json.loads(headers["X-Business-Use-Case-Usage"])
                # Processar informações de uso
                logger.debug(f"📊 Usage info: {usage_info}")

            if "X-App-Usage" in headers:
                app_usage = json.loads(headers["X-App-Usage"])
                if "call_count" in app_usage:
                    self.requests_remaining = 100 - app_usage["call_count"]
                logger.debug(f"📊 App usage: {app_usage}")

        except Exception as e:
            logger.debug(f"Erro ao processar headers de rate limiting: {e}")

    def _handle_rate_limit(self, headers: Dict[str, str]):
        """Processa rate limiting baseado nos headers"""
        try:
            # Tentar obter tempo de reset dos headers
            retry_after = headers.get("Retry-After")
            if retry_after:
                reset_time = datetime.now(timezone.utc) + timedelta(
                    seconds=int(retry_after)
                )
                self.rate_limit_reset_time = reset_time
                self.api_status = MetaAPIStatus.RATE_LIMITED
                logger.warning(f"⏰ Rate limit até {reset_time}")
            else:
                # Fallback: aguardar 1 hora
                self.rate_limit_reset_time = datetime.now(timezone.utc) + timedelta(
                    hours=1
                )
                self.api_status = MetaAPIStatus.RATE_LIMITED

        except Exception as e:
            logger.error(f"Erro ao processar rate limit: {e}")
            # Fallback conservador
            self.rate_limit_reset_time = datetime.now(timezone.utc) + timedelta(hours=1)

    def _calculate_retry_delay(self, attempt: int) -> float:
        """Calcula delay para retry com exponential backoff"""
        delay = self.base_delay * (2**attempt)
        # Adicionar jitter para evitar thundering herd
        jitter = delay * 0.1 * (0.5 - hash(str(time.time())) % 100 / 100)
        return min(delay + jitter, self.max_delay)

    def _add_to_fallback_queue(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]],
        params: Optional[Dict[str, Any]],
    ):
        """Adiciona requisição à fila de fallback"""
        fallback_item = {
            "method": method,
            "endpoint": endpoint,
            "data": data,
            "params": params,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "attempts": 0,
        }

        self.fallback_queue.append(fallback_item)

        # Limitar tamanho da fila
        if len(self.fallback_queue) > 1000:
            self.fallback_queue = self.fallback_queue[-1000:]

        logger.info(f"📥 Adicionado à fila de fallback: {method} {endpoint}")

    async def process_fallback_queue(self):
        """Processa fila de fallback quando API voltar"""
        if not self.fallback_queue or self.api_status != MetaAPIStatus.AVAILABLE:
            return

        logger.info(
            f"🔄 Processando {len(self.fallback_queue)} itens da fila de fallback"
        )

        processed = []
        for item in self.fallback_queue[:10]:  # Processar máximo 10 por vez
            try:
                result = await self.make_api_request(
                    method=item["method"],
                    endpoint=item["endpoint"],
                    data=item["data"],
                    params=item["params"],
                )

                if result:
                    processed.append(item)
                    logger.info(
                        f"✅ Fallback processado: {item['method']} {item['endpoint']}"
                    )
                else:
                    # Se falhar, parar processamento
                    break

            except Exception as e:
                logger.error(f"❌ Erro ao processar fallback: {e}")
                break

        # Remover itens processados
        for item in processed:
            self.fallback_queue.remove(item)

    async def send_message(
        self, phone_number: str, message: str, message_type: str = "text"
    ) -> Optional[Dict[str, Any]]:
        """
        Envia mensagem via WhatsApp Business API com retry e fallback

        Args:
            phone_number: Número do destinatário
            message: Mensagem a enviar
            message_type: Tipo da mensagem

        Returns:
            Resposta da API ou None se falhar
        """
        phone_number_id = getattr(settings, "whatsapp_phone_id", None)

        if not phone_number_id:
            logger.error("❌ WHATSAPP_PHONE_ID não configurado")
            return None

        data = {
            "messaging_product": "whatsapp",
            "to": phone_number,
            "type": message_type,
            message_type: {"body": message},
        }

        result = await self.make_api_request(
            method="POST", endpoint=f"/{phone_number_id}/messages", data=data
        )

        if result:
            logger.info(f"✅ Mensagem enviada para {phone_number}")
        else:
            logger.error(f"❌ Falha ao enviar mensagem para {phone_number}")

        return result

    def get_api_status(self) -> Dict[str, Any]:
        """Retorna status atual da API"""
        return {
            "status": self.api_status.value,
            "requests_remaining": self.requests_remaining,
            "rate_limit_reset": (
                self.rate_limit_reset_time.isoformat()
                if self.rate_limit_reset_time
                else None
            ),
            "fallback_queue_size": len(self.fallback_queue),
        }


# Instância global
whatsapp_security = WhatsAppSecurityService()
