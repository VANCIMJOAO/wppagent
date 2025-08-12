from app.utils.logger import get_logger

logger = get_logger(__name__)
"""
🚀 CDN Manager - Sistema de CDN para Assets Estáticos
Gerencia cache de assets, compressão, e entrega otimizada
"""
import asyncio
import hashlib
import gzip
import mimetypes
import os
from pathlib import Path
from typing import Dict, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging

from fastapi import Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import aiofiles

logger = logging.getLogger(__name__)

@dataclass
class AssetInfo:
    """Informações de um asset"""
    path: str
    content_type: str
    size: int
    etag: str
    last_modified: datetime
    compressed_size: Optional[int] = None
    cache_control: str = "public, max-age=31536000"  # 1 ano padrão

class CDNManager:
    """
    🚀 Gerenciador de CDN para Assets Estáticos
    
    Funcionalidades:
    - Cache agressivo de assets
    - Compressão automática (gzip, brotli)
    - ETags para cache do navegador
    - Headers otimizados
    - Versionamento de assets
    - Pré-compressão de assets
    - Cache warming
    """
    
    def __init__(self, static_dir: str = "app/static"):
        self.static_dir = Path(static_dir)
        self.assets_cache: Dict[str, AssetInfo] = {}
        self.compressed_cache: Dict[str, bytes] = {}
        
        # Configurações de cache por tipo
        self.cache_config = {
            # Assets que mudam pouco - cache longo
            ".css": "public, max-age=31536000, immutable",  # 1 ano
            ".js": "public, max-age=31536000, immutable",   # 1 ano
            ".png": "public, max-age=31536000, immutable",  # 1 ano
            ".jpg": "public, max-age=31536000, immutable",  # 1 ano
            ".jpeg": "public, max-age=31536000, immutable", # 1 ano
            ".gif": "public, max-age=31536000, immutable",  # 1 ano
            ".ico": "public, max-age=31536000, immutable",  # 1 ano
            ".svg": "public, max-age=31536000, immutable",  # 1 ano
            ".woff": "public, max-age=31536000, immutable", # 1 ano
            ".woff2": "public, max-age=31536000, immutable",# 1 ano
            
            # Assets dinâmicos - cache menor
            ".html": "public, max-age=3600, must-revalidate",     # 1 hora
            ".json": "public, max-age=1800, must-revalidate",     # 30 min
            ".xml": "public, max-age=3600, must-revalidate",      # 1 hora
        }
        
        # Tipos que devem ser comprimidos
        self.compressible_types = {
            "text/html", "text/css", "text/javascript",
            "application/javascript", "application/json",
            "text/xml", "application/xml", "text/plain",
            "image/svg+xml"
        }
        
        # Métricas
        self.metrics = {
            "requests": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "bytes_served": 0,
            "compression_savings": 0,
            "assets_cached": 0
        }
        
        logger.info(f"🚀 CDNManager inicializado - Diretório: {self.static_dir}")
    
    async def initialize(self):
        """Inicializa o CDN com warm-up do cache"""
        try:
            # Verificar se diretório existe
            if not self.static_dir.exists():
                self.static_dir.mkdir(parents=True, exist_ok=True)
                logger.warning(f"📁 Diretório estático criado: {self.static_dir}")
            
            # Fazer warm-up do cache
            await self._warm_up_cache()
            
            logger.info("✅ CDNManager inicializado com sucesso")
            
        except Exception as e:
            logger.error(f"❌ Erro ao inicializar CDNManager: {e}")
            raise
    
    async def _warm_up_cache(self):
        """Pré-carrega assets no cache"""
        try:
            asset_count = 0
            
            for file_path in self.static_dir.rglob("*"):
                if file_path.is_file():
                    relative_path = str(file_path.relative_to(self.static_dir))
                    await self._cache_asset(relative_path, file_path)
                    asset_count += 1
            
            self.metrics["assets_cached"] = asset_count
            logger.info(f"🔥 Cache warming concluído: {asset_count} assets carregados")
            
        except Exception as e:
            logger.warning(f"⚠️ Erro no cache warming: {e}")
    
    async def _cache_asset(self, relative_path: str, file_path: Path):
        """Carrega e cacheia um asset"""
        try:
            # Obter informações do arquivo
            stat = file_path.stat()
            content_type, _ = mimetypes.guess_type(str(file_path))
            if not content_type:
                content_type = "application/octet-stream"
            
            # Gerar ETag baseado no conteúdo
            async with aiofiles.open(file_path, 'rb') as f:
                content = await f.read()
            
            etag = hashlib.md5(content).hexdigest()
            
            # Criar info do asset
            asset_info = AssetInfo(
                path=str(file_path),
                content_type=content_type,
                size=len(content),
                etag=etag,
                last_modified=datetime.fromtimestamp(stat.st_mtime),
                cache_control=self._get_cache_control(file_path.suffix)
            )
            
            # Comprimir se aplicável
            if content_type in self.compressible_types:
                compressed = gzip.compress(content, compresslevel=6)
                if len(compressed) < len(content):  # Só usar se realmente economizar
                    asset_info.compressed_size = len(compressed)
                    self.compressed_cache[relative_path] = compressed
                    self.metrics["compression_savings"] += len(content) - len(compressed)
            
            self.assets_cache[relative_path] = asset_info
            
        except Exception as e:
            logger.warning(f"⚠️ Erro ao cachear asset {relative_path}: {e}")
    
    def _get_cache_control(self, file_extension: str) -> str:
        """Retorna cache control baseado na extensão"""
        return self.cache_config.get(file_extension.lower(), "public, max-age=3600")
    
    async def serve_asset(self, request: Request, path: str) -> Response:
        """
        Serve um asset com otimizações de cache
        """
        try:
            self.metrics["requests"] += 1
            
            # Verificar se asset está no cache
            if path not in self.assets_cache:
                # Tentar carregar do disco
                file_path = self.static_dir / path
                if file_path.exists() and file_path.is_file():
                    await self._cache_asset(path, file_path)
                else:
                    return Response(status_code=404, content="Asset not found")
            
            asset_info = self.assets_cache[path]
            
            # Verificar ETag do cliente
            client_etag = request.headers.get("if-none-match")
            if client_etag and client_etag.strip('"') == asset_info.etag:
                return Response(status_code=304)  # Not Modified
            
            # Verificar se cliente aceita compressão
            accept_encoding = request.headers.get("accept-encoding", "")
            use_compression = (
                "gzip" in accept_encoding and 
                path in self.compressed_cache
            )
            
            # Preparar headers
            headers = {
                "Cache-Control": asset_info.cache_control,
                "ETag": f'"{asset_info.etag}"',
                "Last-Modified": asset_info.last_modified.strftime("%a, %d %b %Y %H:%M:%S GMT"),
                "Content-Type": asset_info.content_type
            }
            
            # Servir arquivo
            if use_compression:
                content = self.compressed_cache[path]
                headers["Content-Encoding"] = "gzip"
                headers["Content-Length"] = str(len(content))
                self.metrics["bytes_served"] += len(content)
                self.metrics["cache_hits"] += 1
                
                return Response(
                    content=content,
                    headers=headers,
                    status_code=200
                )
            else:
                # Servir arquivo normal
                self.metrics["bytes_served"] += asset_info.size
                self.metrics["cache_hits"] += 1
                
                return FileResponse(
                    path=asset_info.path,
                    headers=headers,
                    media_type=asset_info.content_type
                )
                
        except Exception as e:
            logger.error(f"❌ Erro ao servir asset {path}: {e}")
            self.metrics["cache_misses"] += 1
            return Response(status_code=500, content="Internal server error")
    
    async def get_asset_url(self, path: str, versioned: bool = True) -> str:
        """
        Retorna URL do asset, opcionalmente com versioning
        """
        if versioned and path in self.assets_cache:
            asset_info = self.assets_cache[path]
            return f"/static/{path}?v={asset_info.etag[:8]}"
        return f"/static/{path}"
    
    async def preload_critical_assets(self) -> str:
        """
        Gera tags de preload para assets críticos
        """
        critical_assets = [
            "dashboard.html",
            "css/dashboard.css",
            "js/dashboard.js"
        ]
        
        preload_tags = []
        for asset in critical_assets:
            if asset in self.assets_cache:
                asset_info = self.assets_cache[asset]
                asset_url = await self.get_asset_url(asset)
                
                # Determinar tipo de preload
                if asset.endswith('.css'):
                    rel_type = "stylesheet"
                elif asset.endswith('.js'):
                    rel_type = "script"
                elif asset.endswith(('.png', '.jpg', '.jpeg', '.webp')):
                    rel_type = "image"
                else:
                    continue
                
                preload_tags.append(
                    f'<link rel="preload" href="{asset_url}" as="{rel_type}">'
                )
        
        return "\n    ".join(preload_tags)
    
    async def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do CDN"""
        total_size = sum(info.size for info in self.assets_cache.values())
        compressed_size = sum(len(data) for data in self.compressed_cache.values())
        
        stats = {
            "assets_cached": len(self.assets_cache),
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / 1024 / 1024, 2),
            "compressed_assets": len(self.compressed_cache),
            "compressed_size_bytes": compressed_size,
            "compressed_size_mb": round(compressed_size / 1024 / 1024, 2),
            "compression_ratio": round((1 - compressed_size / total_size) * 100, 2) if total_size > 0 else 0,
            "metrics": self.metrics.copy(),
            "cache_hit_rate": round(
                self.metrics["cache_hits"] / max(self.metrics["requests"], 1) * 100, 2
            )
        }
        
        return stats
    
    async def clear_cache(self):
        """Limpa todo o cache"""
        self.assets_cache.clear()
        self.compressed_cache.clear()
        logger.info("🧹 Cache de assets limpo")
    
    async def refresh_asset(self, path: str):
        """Recarrega um asset específico"""
        file_path = self.static_dir / path
        if file_path.exists():
            # Remover do cache
            if path in self.assets_cache:
                del self.assets_cache[path]
            if path in self.compressed_cache:
                del self.compressed_cache[path]
            
            # Recarregar
            await self._cache_asset(path, file_path)
            logger.info(f"🔄 Asset recarregado: {path}")
        else:
            logger.warning(f"⚠️ Asset não encontrado para recarregar: {path}")

class OptimizedStaticFiles(StaticFiles):
    """
    Versão otimizada do StaticFiles com CDN integrado
    """
    
    def __init__(self, cdn_manager: CDNManager, **kwargs):
        super().__init__(**kwargs)
        self.cdn_manager = cdn_manager
    
    async def __call__(self, scope, receive, send):
        """Handle request com otimizações de CDN"""
        from fastapi import Request
        
        request = Request(scope, receive)
        path = request.path_params.get("path", "")
        
        # Usar CDN manager para servir
        response = await self.cdn_manager.serve_asset(request, path)
        await response(scope, receive, send)

# Instância global
cdn_manager = CDNManager()
