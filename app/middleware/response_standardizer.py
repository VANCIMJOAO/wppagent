"""
🔧 C002 - Response Standardizer Middleware
==========================================

Middleware para padronizar respostas da API seguindo o padrão:
{
    "success": true|false,
    "data": any,
    "error": string|null
}
"""

import json
import logging
from typing import Any, Dict, Optional, Union

from fastapi import HTTPException, Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


class ApiResponseMiddleware(BaseHTTPMiddleware):
    """
    C002 - Middleware para padronizar respostas da API

    Converte todas as respostas para o formato padrão:
    - success: boolean indicando se a operação foi bem-sucedida
    - data: dados retornados (se sucesso)
    - error: mensagem de erro (se falha)
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.excluded_paths = {
            "/docs",
            "/redoc",
            "/openapi.json",
            "/health",
            "/ping",  # Railway healthcheck endpoint
            "/static",
            "/webhook",  # Webhook precisa retornar formato específico
            "/meta",  # Meta webhook endpoints
        }

    async def dispatch(self, request: Request, call_next):
        """Processar requisição e padronizar resposta"""

        # Pular padronização para paths excluídos
        if any(request.url.path.startswith(path) for path in self.excluded_paths):
            return await call_next(request)

        try:
            # Executar a requisição
            response = await call_next(request)

            # Padronizar apenas respostas JSON
            if response.headers.get("content-type", "").startswith("application/json"):
                return await self._standardize_response(response)

            return response

        except HTTPException as e:
            # Padronizar erros HTTP
            return self._create_error_response(e.status_code, e.detail)
        except Exception as e:
            # Padronizar erros internos
            logger.error(f"C002 - Erro interno: {e}")
            return self._create_error_response(500, "Internal server error")

    async def _standardize_response(self, response: Response) -> JSONResponse:
        """Padronizar resposta para formato padrão"""

        # Ler conteúdo da resposta
        body = b""
        async for chunk in response.body_iterator:
            body += chunk

        try:
            # Tentar parsear JSON existente
            original_data = json.loads(body.decode())

            # Se já está no formato padrão, retornar como está
            if isinstance(original_data, dict) and "success" in original_data:
                # Copy headers but exclude Content-Length to let FastAPI recalculate it
                headers = {
                    k: v
                    for k, v in response.headers.items()
                    if k.lower() != "content-length"
                }

                return JSONResponse(
                    content=original_data,
                    status_code=response.status_code,
                    headers=headers,
                )

            # Padronizar para formato padrão
            standardized = self._create_success_response(original_data)

            # Copy headers but exclude Content-Length to let FastAPI recalculate it
            headers = {
                k: v
                for k, v in response.headers.items()
                if k.lower() != "content-length"
            }

            return JSONResponse(
                content=standardized, status_code=response.status_code, headers=headers
            )

        except (json.JSONDecodeError, UnicodeDecodeError):
            # Se não conseguir parsear, retornar como sucesso com dados raw
            # Copy headers but exclude Content-Length to let FastAPI recalculate it
            headers = {
                k: v
                for k, v in response.headers.items()
                if k.lower() != "content-length"
            }

            return JSONResponse(
                content=self._create_success_response({"raw": body.decode()}),
                status_code=response.status_code,
                headers=headers,
            )

    def _create_success_response(self, data: Any) -> Dict[str, Any]:
        """Criar resposta de sucesso padronizada"""
        return {"success": True, "data": data, "error": None}

    def _create_error_response(
        self, status_code: int, error_message: str
    ) -> JSONResponse:
        """Criar resposta de erro padronizada"""
        return JSONResponse(
            content={"success": False, "data": None, "error": error_message},
            status_code=status_code,
        )


class ResponseStandardizerConfig:
    """Configuração para o middleware de padronização"""

    @staticmethod
    def get_excluded_paths() -> set:
        """Obter paths que devem ser excluídos da padronização"""
        return {
            "/docs",
            "/redoc",
            "/openapi.json",
            "/health",
            "/ping",  # Railway healthcheck endpoint
            "/static",
            "/webhook",
            "/meta",  # Meta webhook endpoints
            "/metrics",
            "/favicon.ico",
        }

    @staticmethod
    def should_standardize(request: Request) -> bool:
        """Verificar se a requisição deve ser padronizada"""
        excluded_paths = ResponseStandardizerConfig.get_excluded_paths()
        return not any(request.url.path.startswith(path) for path in excluded_paths)


def create_standardized_response(
    success: bool, data: Any = None, error: Optional[str] = None
) -> Dict[str, Any]:
    """
    Função helper para criar respostas padronizadas manualmente

    Args:
        success: Se a operação foi bem-sucedida
        data: Dados a retornar (se sucesso)
        error: Mensagem de erro (se falha)

    Returns:
        Dicionário no formato padrão
    """
    return {
        "success": success,
        "data": data if success else None,
        "error": error if not success else None,
    }
