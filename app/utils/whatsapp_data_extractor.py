"""
🔧 EXTRATOR DE DADOS WHATSAPP
============================

Função para extrair wa_id, clean_content e contact_info de dados do WhatsApp.
"""

import logging
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger(__name__)


def sanitize_whatsapp_data(message_data: Dict[str, Any]) -> Tuple[Optional[str], Optional[str], Dict[str, Any]]:
    """
    Extrai e sanitiza dados essenciais de uma mensagem do WhatsApp
    
    Args:
        message_data: Dados da mensagem do WhatsApp
        
    Returns:
        Tuple[wa_id, clean_content, contact_info]:
            - wa_id: ID do WhatsApp (telefone)
            - clean_content: Conteúdo da mensagem sanitizado
            - contact_info: Informações do contato
    """
    try:
        # Extrair wa_id
        wa_id = message_data.get("from")
        if not wa_id:
            logger.warning("Mensagem sem 'from' (wa_id)")
            return None, None, {}
        
        # Extrair conteúdo da mensagem
        clean_content = None
        message_type = message_data.get("type", "text")
        
        if message_type == "text" and "text" in message_data:
            clean_content = message_data["text"].get("body", "")
        elif message_type == "image" and "image" in message_data:
            clean_content = f"[Imagem: {message_data['image'].get('caption', 'Sem legenda')}]"
        elif message_type == "audio" and "audio" in message_data:
            clean_content = "[Áudio]"
        elif message_type == "video" and "video" in message_data:
            clean_content = f"[Vídeo: {message_data['video'].get('caption', 'Sem legenda')}]"
        elif message_type == "document" and "document" in message_data:
            clean_content = f"[Documento: {message_data['document'].get('filename', 'Arquivo')}]"
        else:
            clean_content = f"[{message_type.upper()}]"
        
        if not clean_content:
            logger.warning(f"Mensagem {message_type} sem conteúdo extraível")
            return wa_id, None, {}
        
        # Extrair informações do contato
        contact_info = {}
        
        # Buscar informações do contato no contexto da mensagem
        if "context" in message_data and "from" in message_data["context"]:
            contact_info["wa_id"] = message_data["context"]["from"]
        
        # Adicionar informações básicas
        contact_info["message_id"] = message_data.get("id")
        contact_info["message_type"] = message_type
        contact_info["timestamp"] = message_data.get("timestamp")
        
        logger.debug(f"Dados extraídos: wa_id={wa_id}, content={clean_content[:50]}...")
        
        return wa_id, clean_content, contact_info
        
    except Exception as e:
        logger.error(f"Erro ao extrair dados do WhatsApp: {e}")
        return None, None, {}


def sanitize_phone(phone: str) -> str:
    """
    Sanitiza número de telefone para formato brasileiro
    
    Args:
        phone: Número de telefone bruto
        
    Returns:
        str: Número sanitizado
    """
    if not phone:
        return ""
    
    # Remover caracteres não numéricos
    clean_phone = "".join(filter(str.isdigit, phone))
    
    # Adicionar código do país se necessário
    if clean_phone.startswith("55"):
        return clean_phone
    elif len(clean_phone) == 11 and clean_phone.startswith("1"):
        return f"55{clean_phone}"
    elif len(clean_phone) == 10:
        return f"551{clean_phone}"
    else:
        return clean_phone


def sanitize_message(content: str, message_type: str = "text") -> str:
    """
    Sanitiza conteúdo da mensagem
    
    Args:
        content: Conteúdo da mensagem
        message_type: Tipo da mensagem
        
    Returns:
        str: Conteúdo sanitizado
    """
    if not content:
        return ""
    
    # Limitar tamanho
    if len(content) > 4096:
        content = content[:4096]
    
    # Remover caracteres de controle perigosos
    content = content.replace("\x00", "").replace("\r", "")
    
    return content.strip()
