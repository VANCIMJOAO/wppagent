from app.utils.logger import get_logger

logger = get_logger(__name__)
"""
🧹 SISTEMA AVANÇADO DE SANITIZAÇÃO DE DADOS WHATSAPP

Sistema completo de sanitização e validação de dados recebidos do WhatsApp
para prevenir vulnerabilidades de segurança e garantir integridade dos dados.

Autor: WhatsApp Agent Security Team
Data: 08 de Agosto de 2025
Versão: 1.0.0
"""

import re
import json
import html
import logging
from typing import Dict, Any, List, Optional, Union, Tuple
from datetime import datetime
from urllib.parse import unquote, quote
from pathlib import Path

logger = logging.getLogger(__name__)

class WhatsAppSanitizer:
    """
    Classe principal para sanitização robusta de dados do WhatsApp
    """
    
    # Padrões de expressões regulares para validação
    PATTERNS = {
        'phone_number': r'^55\d{2}9?\d{8}$',  # Formato brasileiro WhatsApp
        'message_id': r'^[a-zA-Z0-9_\-]{1,100}$',
        'safe_text': r'^[a-zA-Z0-9\s\u00C0-\u024F\u1E00-\u1EFF\U0001F000-\U0001F9FF\U00002000-\U000027BF\U0000FE00-\U0000FE0F.,!?:;\-_@#$%&*()\[\]{}="\'\/\\+\n\r\t•]{0,4096}$',
        'url': r'^https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)$',
        'email': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
        'filename': r'^[a-zA-Z0-9._\-]{1,255}$'
    }
    
    # Caracteres perigosos para remoção/escape
    DANGEROUS_CHARS = {
        'sql_injection': [';', '--', '/*', '*/', 'xp_', 'sp_', 'DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'CREATE', 'EXEC'],
        'xss': ['<script', '</script>', '<iframe', '<object', '<embed', '<link', '<meta', 'javascript:', 'vbscript:', 'onload=', 'onclick=', 'onerror='],
        'command_injection': ['|', '&', ';', '$', '`', '$(', '${', '&&', '||'],  # 🔥 CORREÇÃO: Removido '\n' e '\r' 
        'path_traversal': ['../', '..\\', '/etc/', '/var/', '/usr/', '/bin/', '/sbin/', 'C:\\', 'D:\\']
    }
    
    # Tipos de arquivo permitidos
    ALLOWED_FILE_TYPES = {
        'image': ['jpg', 'jpeg', 'png', 'gif', 'webp'],
        'document': ['pdf', 'doc', 'docx', 'txt'],
        'audio': ['mp3', 'wav', 'ogg', 'm4a'],
        'video': ['mp4', 'avi', 'mov', 'webm']
    }
    
    # Limites de tamanho
    LIMITS = {
        'text_message': 4096,
        'contact_name': 200,
        'media_caption': 1024,
        'filename': 255,
        'payload_size': 10 * 1024 * 1024,  # 10MB
        'media_size': 16 * 1024 * 1024     # 16MB
    }
    
    @classmethod
    def sanitize_whatsapp_payload(cls, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitiza payload completo do webhook WhatsApp
        
        Args:
            payload: Payload bruto recebido do WhatsApp
            
        Returns:
            Dict[str, Any]: Payload sanitizado
            
        Raises:
            ValueError: Se payload for inválido ou malicioso
        """
        try:
            logger.debug("🧹 Iniciando sanitização de payload WhatsApp")
            
            # Verificar se payload é válido
            if not isinstance(payload, dict):
                raise ValueError("Payload deve ser um dicionário")
            
            # Verificar tamanho do payload
            payload_str = json.dumps(payload)
            if len(payload_str) > cls.LIMITS['payload_size']:
                raise ValueError(f"Payload muito grande: {len(payload_str)} bytes")
            
            # Sanitizar recursivamente
            sanitized = cls._sanitize_dict_recursive(payload)
            
            # Validações específicas do WhatsApp
            cls._validate_whatsapp_structure(sanitized)
            
            logger.debug("✅ Payload WhatsApp sanitizado com sucesso")
            return sanitized
            
        except Exception as e:
            logger.error(f"❌ Erro na sanitização do payload: {e}")
            raise ValueError(f"Falha na sanitização: {str(e)}")
    
    @classmethod
    def sanitize_message_content(cls, content: str, message_type: str = "text") -> str:
        """
        Sanitiza conteúdo de mensagem WhatsApp
        
        Args:
            content: Conteúdo da mensagem
            message_type: Tipo da mensagem (text, image, document, etc.)
            
        Returns:
            str: Conteúdo sanitizado
        """
        try:
            if not content or not isinstance(content, str):
                return ""
            
            # Verificar tamanho
            max_length = cls.LIMITS.get('text_message', 4096)
            if len(content) > max_length:
                content = content[:max_length]
                logger.warning(f"⚠️ Conteúdo truncado para {max_length} caracteres")
            
            # Sanitizar caracteres perigosos
            sanitized = cls._remove_dangerous_content(content)
            
            # Sanitização específica por tipo
            if message_type == "text":
                sanitized = cls._sanitize_text_message(sanitized)
            elif message_type in ["image", "document", "audio", "video"]:
                sanitized = cls._sanitize_media_caption(sanitized)
            
            # Normalizar espaços e quebras de linha
            # 🔥 CORREÇÃO: Usar sanitização que preserva formatação
            sanitized = cls._normalize_whitespace_preserve_formatting(sanitized)
            
            return sanitized
            
        except Exception as e:
            logger.error(f"❌ Erro na sanitização do conteúdo: {e}")
            return ""  # Retornar string vazia em caso de erro
    
    @classmethod
    def sanitize_phone_number(cls, phone: str) -> str:
        """
        Sanitiza e valida número de telefone WhatsApp
        
        Args:
            phone: Número de telefone bruto
            
        Returns:
            str: Número sanitizado no formato WhatsApp
            
        Raises:
            ValueError: Se número for inválido
        """
        try:
            if not phone or not isinstance(phone, str):
                raise ValueError("Número de telefone inválido")
            
            # Remover caracteres não numéricos
            clean_phone = re.sub(r'[^\d]', '', phone)
            
            # Remover sufixos do WhatsApp
            clean_phone = clean_phone.replace("@c.us", "").replace("@s.whatsapp.net", "")
            
            # Normalizar para formato brasileiro
            if len(clean_phone) == 11 and not clean_phone.startswith('55'):
                clean_phone = f"55{clean_phone}"
            elif len(clean_phone) == 10:
                # Adicionar 9 no celular se necessário
                ddd = clean_phone[:2]
                if clean_phone[2] in '6789':
                    clean_phone = f"55{ddd}9{clean_phone[2:]}"
                else:
                    clean_phone = f"55{clean_phone}"
            
            # Validar formato final
            if not re.match(cls.PATTERNS['phone_number'], clean_phone):
                raise ValueError(f"Formato de telefone inválido: {clean_phone}")
            
            # Validar DDD brasileiro
            ddd = clean_phone[2:4]
            if not (11 <= int(ddd) <= 99):
                raise ValueError(f"DDD brasileiro inválido: {ddd}")
            
            return clean_phone
            
        except Exception as e:
            logger.error(f"❌ Erro na sanitização do telefone {phone}: {e}")
            raise ValueError(f"Telefone inválido: {str(e)}")
    
    @classmethod
    def sanitize_contact_info(cls, contact: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitiza informações de contato
        
        Args:
            contact: Dados do contato
            
        Returns:
            Dict[str, Any]: Contato sanitizado
        """
        try:
            sanitized = {}
            
            # Sanitizar wa_id
            if 'wa_id' in contact:
                sanitized['wa_id'] = cls.sanitize_phone_number(contact['wa_id'])
            
            # Sanitizar nome do perfil
            if 'profile' in contact and isinstance(contact['profile'], dict):
                profile = contact['profile']
                if 'name' in profile:
                    name = cls._sanitize_contact_name(profile['name'])
                    if name:  # Só incluir se o nome for válido
                        sanitized['profile'] = {'name': name}
            
            return sanitized
            
        except Exception as e:
            logger.error(f"❌ Erro na sanitização do contato: {e}")
            return {}
    
    @classmethod
    def sanitize_media_info(cls, media: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitiza informações de mídia
        
        Args:
            media: Dados da mídia
            
        Returns:
            Dict[str, Any]: Mídia sanitizada
        """
        try:
            sanitized = {}
            
            # Sanitizar ID da mídia
            if 'id' in media:
                media_id = str(media['id'])
                if re.match(r'^[a-zA-Z0-9_\-]{1,100}$', media_id):
                    sanitized['id'] = media_id
            
            # Sanitizar mime type
            if 'mime_type' in media:
                mime_type = cls._sanitize_mime_type(media['mime_type'])
                if mime_type:
                    sanitized['mime_type'] = mime_type
            
            # Sanitizar filename
            if 'filename' in media:
                filename = cls._sanitize_filename(media['filename'])
                if filename:
                    sanitized['filename'] = filename
            
            # Sanitizar caption
            if 'caption' in media:
                caption = cls.sanitize_message_content(media['caption'], 'media')
                if caption:
                    sanitized['caption'] = caption
            
            # Validar tamanho se disponível
            if 'filesize' in media:
                try:
                    filesize = int(media['filesize'])
                    if 0 < filesize <= cls.LIMITS['media_size']:
                        sanitized['filesize'] = filesize
                except (ValueError, TypeError):
                    pass
            
            return sanitized
            
        except Exception as e:
            logger.error(f"❌ Erro na sanitização da mídia: {e}")
            return {}
    
    @classmethod
    def validate_webhook_signature(cls, signature: str, payload: str, webhook_secret: str) -> bool:
        """
        Valida assinatura do webhook WhatsApp
        
        Args:
            signature: Assinatura recebida
            payload: Payload da requisição
            webhook_secret: Segredo do webhook
            
        Returns:
            bool: True se assinatura for válida
        """
        try:
            import hmac
            import hashlib
            
            if not signature or not payload or not webhook_secret:
                return False
            
            # Remover prefixo "sha256=" se presente
            if signature.startswith('sha256='):
                signature = signature[7:]
            
            # Calcular hash esperado
            expected_hash = hmac.new(
                webhook_secret.encode('utf-8'),
                payload.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            # Comparação segura contra timing attacks
            return hmac.compare_digest(signature, expected_hash)
            
        except Exception as e:
            logger.error(f"❌ Erro na validação da assinatura: {e}")
            return False
    
    @classmethod
    def _sanitize_dict_recursive(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitiza dicionário recursivamente"""
        sanitized = {}
        
        for key, value in data.items():
            # Sanitizar chave
            safe_key = cls._sanitize_string_key(key)
            
            if isinstance(value, dict):
                sanitized[safe_key] = cls._sanitize_dict_recursive(value)
            elif isinstance(value, list):
                sanitized[safe_key] = cls._sanitize_list_recursive(value)
            elif isinstance(value, str):
                sanitized[safe_key] = cls._sanitize_string_value(value)
            elif isinstance(value, (int, float, bool)):
                sanitized[safe_key] = value
            elif value is None:
                sanitized[safe_key] = None
            else:
                # Converter outros tipos para string e sanitizar
                sanitized[safe_key] = cls._sanitize_string_value(str(value))
        
        return sanitized
    
    @classmethod
    def _sanitize_list_recursive(cls, data: List[Any]) -> List[Any]:
        """Sanitiza lista recursivamente"""
        sanitized = []
        
        for item in data:
            if isinstance(item, dict):
                sanitized.append(cls._sanitize_dict_recursive(item))
            elif isinstance(item, list):
                sanitized.append(cls._sanitize_list_recursive(item))
            elif isinstance(item, str):
                sanitized.append(cls._sanitize_string_value(item))
            elif isinstance(item, (int, float, bool)):
                sanitized.append(item)
            elif item is None:
                sanitized.append(None)
            else:
                sanitized.append(cls._sanitize_string_value(str(item)))
        
        return sanitized
    
    @classmethod
    def _sanitize_string_key(cls, key: str) -> str:
        """Sanitiza chave de dicionário"""
        if not isinstance(key, str):
            key = str(key)
        
        # Remover caracteres perigosos de chaves
        key = re.sub(r'[^\w\-_.]', '', key)
        
        # Limitar tamanho
        if len(key) > 100:
            key = key[:100]
        
        return key if key else "unknown_key"
    
    @classmethod
    def _sanitize_string_value(cls, value: str) -> str:
        """Sanitiza valor string"""
        if not isinstance(value, str):
            value = str(value)
        
        # Limitar tamanho
        if len(value) > 10000:  # Limite geral para valores
            value = value[:10000]
        
        # Remover caracteres de controle perigosos
        value = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', value)
        
        # HTML escape básico
        value = html.escape(value, quote=True)
        
        return value
    
    @classmethod
    def _validate_whatsapp_structure(cls, payload: Dict[str, Any]) -> None:
        """Valida estrutura básica do payload WhatsApp"""
        # Verificar se tem estrutura básica do WhatsApp
        if 'entry' not in payload:
            return  # Pode ser verificação do webhook
        
        if not isinstance(payload['entry'], list):
            raise ValueError("Campo 'entry' deve ser uma lista")
        
        for entry in payload['entry']:
            if not isinstance(entry, dict):
                raise ValueError("Entradas devem ser dicionários")
            
            if 'changes' in entry:
                if not isinstance(entry['changes'], list):
                    raise ValueError("Campo 'changes' deve ser uma lista")
    
    @classmethod
    def _remove_dangerous_content(cls, content: str) -> str:
        """Remove conteúdo perigoso"""
        if not content:
            return ""
        
        # Remover todas as tags HTML/XML de forma mais robusta
        # Remove tags completas primeiro
        content = re.sub(r'<[^>]*>', '', content)
        
        # Remove tentativas de abertura de tags sem fechamento
        content = re.sub(r'<[^<]*$', '', content)
        
        # Remove padrões de SQL injection
        for pattern in cls.DANGEROUS_CHARS['sql_injection']:
            content = content.replace(pattern, '')
        
        # Remover padrões de XSS mais robustamente
        xss_patterns = [
            r'javascript\s*:',
            r'vbscript\s*:',
            r'data\s*:',
            r'on\w+\s*=',
            r'eval\s*\(',
            r'expression\s*\(',
            r'script\b',
            r'iframe\b',
            r'object\b',
            r'embed\b',
            r'form\b',
            r'input\b',
        ]
        
        for pattern in xss_patterns:
            content = re.sub(pattern, '', content, flags=re.IGNORECASE)
        
        # Remover padrões originais de XSS também
        for pattern in cls.DANGEROUS_CHARS['xss']:
            content = re.sub(re.escape(pattern), '', content, flags=re.IGNORECASE)
        
        # Remover padrões de command injection
        for pattern in cls.DANGEROUS_CHARS['command_injection']:
            content = content.replace(pattern, '')
        
        # Remover padrões de path traversal
        for pattern in cls.DANGEROUS_CHARS['path_traversal']:
            content = content.replace(pattern, '')
        
        # Escapar caracteres HTML restantes
        content = content.replace('&', '&amp;')
        content = content.replace('<', '&lt;')
        content = content.replace('>', '&gt;')
        content = content.replace('"', '&quot;')
        content = content.replace("'", '&#x27;')
        
        return content
    
    @classmethod
    def _sanitize_text_message(cls, text: str) -> str:
        """Sanitização específica para mensagens de texto"""
        if not text:
            return ""
        
        # Validar caracteres permitidos
        if not re.match(cls.PATTERNS['safe_text'], text):
            # Remover caracteres não permitidos (mantendo emojis)
            text = re.sub(r'[^\w\s\u00C0-\u024F\u1E00-\u1EFF\U0001F000-\U0001F9FF\U00002000-\U000027BF\U0000FE00-\U0000FE0F.,!?:;\-_@#$%&*()\[\]{}="\'\/\\+\n\r\t•]', '', text)
        
        # Limitar tamanho
        if len(text) > cls.LIMITS['text_message']:
            text = text[:cls.LIMITS['text_message']]
        
        # 🔥 CORREÇÃO: NÃO usar strip() que remove quebras de linha importantes
        return text
    
    @classmethod
    def _sanitize_media_caption(cls, caption: str) -> str:
        """Sanitização específica para legendas de mídia"""
        if not caption:
            return ""
        
        # Limitar tamanho
        if len(caption) > cls.LIMITS['media_caption']:
            caption = caption[:cls.LIMITS['media_caption']]
        
        # Remover caracteres perigosos
        caption = cls._remove_dangerous_content(caption)
        
        # 🔥 CORREÇÃO: NÃO usar strip() para preservar formatação
        return caption
    
    @classmethod
    def _sanitize_contact_name(cls, name: str) -> str:
        """Sanitização específica para nome de contato"""
        if not name or not isinstance(name, str):
            return ""
        
        # Limitar tamanho
        if len(name) > cls.LIMITS['contact_name']:
            name = name[:cls.LIMITS['contact_name']]
        
        # Permitir apenas caracteres seguros para nomes
        name = re.sub(r'[^\w\s\u00C0-\u024F\u1E00-\u1EFF.\-]', '', name)
        
        return name.strip()
    
    @classmethod
    def _sanitize_filename(cls, filename: str) -> str:
        """Sanitização específica para nomes de arquivo"""
        if not filename or not isinstance(filename, str):
            return ""
        
        # Limitar tamanho
        if len(filename) > cls.LIMITS['filename']:
            filename = filename[:cls.LIMITS['filename']]
        
        # Validar padrão de filename seguro
        if not re.match(cls.PATTERNS['filename'], filename):
            # Remover caracteres perigosos
            filename = re.sub(r'[^\w.\-]', '_', filename)
        
        # Remover path traversal
        filename = filename.replace('..', '').replace('/', '').replace('\\', '')
        
        return filename
    
    @classmethod
    def _sanitize_mime_type(cls, mime_type: str) -> str:
        """Sanitização específica para tipos MIME"""
        if not mime_type or not isinstance(mime_type, str):
            return ""
        
        # Lista de MIME types permitidos
        allowed_mimes = [
            'text/plain', 'text/html',
            'image/jpeg', 'image/png', 'image/gif', 'image/webp',
            'audio/mpeg', 'audio/wav', 'audio/ogg', 'audio/m4a',
            'video/mp4', 'video/avi', 'video/mov', 'video/webm',
            'application/pdf', 'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        ]
        
        mime_type = mime_type.lower().strip()
        
        if mime_type in allowed_mimes:
            return mime_type
        
        return ""
    
    @classmethod
    def _normalize_whitespace(cls, text: str) -> str:
        """Normaliza espaços em branco"""
        if not text:
            return ""
        
        # Substituir múltiplos espaços por um único
        text = re.sub(r' +', ' ', text)
        
        # Limitar quebras de linha consecutivas
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Remover espaços no início e fim
        text = text.strip()
        
        return text
    
    @classmethod
    def _normalize_whitespace_preserve_formatting(cls, text: str) -> str:
        """
        🔥 CORREÇÃO: Normaliza espaços mas PRESERVA formatação WhatsApp
        
        Esta função mantém as quebras de linha necessárias para formatação
        """
        if not text:
            return ""
        
        # Substituir múltiplos espaços por um único (exceto quebras de linha)
        text = re.sub(r'[^\S\n]+', ' ', text)
        
        # Limitar quebras de linha consecutivas para máximo 2
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # 🔥 CRÍTICO: NÃO usar strip() que remove quebras importantes
        # Apenas remover espaços no início e fim de cada linha
        lines = text.split('\n')
        lines = [line.rstrip() for line in lines]  # Remove espaços no final de cada linha
        text = '\n'.join(lines)
        
        return text


class WhatsAppSecurityValidator:
    """
    Validador de segurança específico para dados WhatsApp
    """
    
    @staticmethod
    def is_potential_spam(content: str) -> bool:
        """Detecta possível spam"""
        if not content:
            return False
        
        # Padrões de spam mais abrangentes
        spam_patterns = [
            r'http[s]?://bit\.ly',           # Links encurtados
            r'telegram\.me',                 # Links Telegram
            r'whatsapp\.com/join',           # Links de grupo
            r'\b(free|gratis|gratuito).*(money|dinheiro|cash|premio)\b',
            r'\b(urgent|urgente).*(action|acao|click|now|agora)\b',
            r'\b(limited time|tempo limitado|oferta limitada)\b',
            r'\b(click here|clique aqui|acesse|visit)\b',
            r'\b(verify account|verificar conta|confirm|confirme)\b',
            r'\b(winner|ganhador|premio|won|ganhou)\b',
            r'\b(congratulations|parabens|selected|selecionado)\b',
            r'\b(lottery|loteria|promo|promocao)\b',
            r'\bmulti.?level.?marketing\b',
            r'\bpyramid.?scheme\b',
            r'\bget.?rich.?quick\b',
            r'\bmake.?money.?(fast|easy|facil)\b',
            r'\b(guaranteed|garantido).*(profit|lucro|income)\b',
            r'\b(investment|investimento).*(risk.?free|sem.?risco)\b',
            r'\b(earn|ganhe).*(from.?home|de.?casa)\b',
            r'\b(no.?experience|sem.?experiencia).*(required|necessaria)\b',
            r'\b(double|triple).*(money|dinheiro)\b'
        ]
        
        content_lower = content.lower()
        
        for pattern in spam_patterns:
            if re.search(pattern, content_lower, re.IGNORECASE):
                return True
        
        # Verificar excesso de emojis
        emoji_count = len(re.findall(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]', content))
        if emoji_count > len(content) * 0.3:  # Mais de 30% emojis
            return True
        
        # Verificar repetições excessivas
        if re.search(r'(.)\1{10,}', content):  # Mesmo caractere 10+ vezes
            return True
        
        # Verifica excesso de maiúsculas (mais de 70% do texto)
        if len(content) > 10:
            uppercase_count = sum(1 for c in content if c.isupper())
            uppercase_ratio = uppercase_count / len(content)
            if uppercase_ratio > 0.7:
                return True
        
        # Verifica excesso de caracteres especiais (!?.)
        special_count = content.count('!') + content.count('?') + content.count('.')
        if special_count > 5:
            return True
        
        # Verifica URLs suspeitas múltiplas
        url_count = len(re.findall(r'http[s]?://|www\.', content_lower))
        if url_count > 2:
            return True
        
        return False
        
        # Verifica excesso de caracteres especiais (!?.)
        special_count = content.count('!') + content.count('?') + content.count('.')
        if special_count > 5:
            return True
        
        # Verifica URLs suspeitas múltiplas
        url_count = len(re.findall(r'http[s]?://|www\.', content_lower))
        if url_count > 2:
            return True
            return True
        
        return False
    
    @staticmethod
    def is_potential_phishing(content: str) -> bool:
        """Detecta possível phishing"""
        if not content:
            return False
        
        phishing_patterns = [
            r'verify.*account',
            r'suspended.*account',
            r'click.*link.*verify',
            r'urgent.*security',
            r'bank.*verification',
            r'paypal.*confirm',
            r'amazon.*security',
            r'microsoft.*verify'
        ]
        
        content_lower = content.lower()
        
        for pattern in phishing_patterns:
            if re.search(pattern, content_lower):
                return True
        
        return False
    
    @staticmethod
    def is_potential_malware(filename: str, mime_type: str) -> bool:
        """Detecta possível malware"""
        if not filename and not mime_type:
            return False
        
        # Extensões perigosas
        dangerous_extensions = [
            '.exe', '.bat', '.cmd', '.com', '.scr', '.pif',
            '.vbs', '.js', '.jar', '.apk', '.dex'
        ]
        
        if filename:
            filename_lower = filename.lower()
            for ext in dangerous_extensions:
                if filename_lower.endswith(ext):
                    return True
        
        # MIME types perigosos
        dangerous_mimes = [
            'application/x-executable',
            'application/x-msdownload',
            'application/x-msdos-program',
            'application/x-javascript',
            'text/javascript'
        ]
        
        if mime_type and mime_type.lower() in dangerous_mimes:
            return True
        
        return False


# Instância global do sanitizador
whatsapp_sanitizer = WhatsAppSanitizer()
security_validator = WhatsAppSecurityValidator()

# Funções de conveniência
def sanitize_whatsapp_data(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Função de conveniência para sanitizar dados WhatsApp"""
    return whatsapp_sanitizer.sanitize_whatsapp_payload(payload)

def sanitize_message(content: str, message_type: str = "text") -> str:
    """Função de conveniência para sanitizar mensagem"""
    return whatsapp_sanitizer.sanitize_message_content(content, message_type)

def sanitize_phone(phone: str) -> str:
    """Função de conveniência para sanitizar telefone"""
    return whatsapp_sanitizer.sanitize_phone_number(phone)

def validate_security(content: str, filename: str = None, mime_type: str = None) -> Dict[str, bool]:
    """Função de conveniência para validar segurança"""
    return {
        'is_spam': security_validator.is_potential_spam(content),
        'is_phishing': security_validator.is_potential_phishing(content),
        'is_malware': security_validator.is_potential_malware(filename or "", mime_type or "")
    }

logger.info("✅ Sistema de sanitização WhatsApp inicializado com sucesso")
