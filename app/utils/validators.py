from app.utils.logger import get_logger

logger = get_logger(__name__)
"""
Validadores e utilitários para dados brasileiros e validação robusta do sistema
"""
import re
import json
import logging
from typing import Tuple, Any, Dict, List, Optional, Union
from datetime import datetime, timedelta
from sqlalchemy import text

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ValidationError(Exception):
    """Exceção personalizada para erros de validação"""
    pass

class RobustValidator:
    """Classe principal para validação robusta de dados"""
    
    # Padrões regex para validação
    PATTERNS = {
        'email': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
        'name': r'^[a-zA-Z\s\u00C0-\u024F\u1E00-\u1EFF]{2,100}$',  # Suporte a acentos
        'username': r'^[a-zA-Z0-9_]{3,30}$',
        'password': r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[a-zA-Z\d@$!%*?&]{8,}$',
        'url': r'^https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)$',
        'token': r'^[a-zA-Z0-9_\-]{10,}$',
        'conversation_id': r'^\d+$',
        'message_id': r'^\d+$',
        'user_id': r'^\d+$',
        'appointment_id': r'^\d+$',
        'service_id': r'^\d+$'
    }
    
    # Limites de tamanho
    LIMITS = {
        'name_min': 2,
        'name_max': 100,
        'message_max': 4096,  # WhatsApp message limit
        'notes_max': 1000,
        'description_max': 500,
        'price_min': 0,
        'price_max': 999999.99,
        'duration_min': 1,
        'duration_max': 480  # 8 horas em minutos
    }
    
    # Status válidos
    VALID_STATUS = {
        'conversation': ['ativa', 'pausada', 'finalizada', 'bloqueada'],
        'appointment': ['agendado', 'confirmado', 'em_andamento', 'concluido', 'cancelado', 'nao_compareceu'],
        'message': ['enviada', 'entregue', 'lida', 'falhada'],
        'user': ['ativo', 'inativo', 'bloqueado'],
        'service': ['ativo', 'inativo', 'manutencao']
    }
    
    @staticmethod
    def validate_string(value: Any, field_name: str, min_length: int = 0, max_length: int = 255, 
                       pattern: Optional[str] = None, required: bool = True) -> str:
        """Validar string com parâmetros customizáveis"""
        try:
            # Verificar se é obrigatório
            if required and (value is None or value == ""):
                raise ValidationError(f"❌ {field_name} é obrigatório")
            
            # Se não é obrigatório e está vazio, retornar string vazia
            if not required and (value is None or value == ""):
                return ""
            
            # Converter para string e limpar
            str_value = str(value).strip()
            
            # Verificar comprimento
            if len(str_value) < min_length:
                raise ValidationError(f"❌ {field_name} deve ter pelo menos {min_length} caracteres")
            
            if len(str_value) > max_length:
                raise ValidationError(f"❌ {field_name} deve ter no máximo {max_length} caracteres")
            
            # Verificar padrão regex se fornecido
            if pattern and not re.match(pattern, str_value):
                raise ValidationError(f"❌ {field_name} possui formato inválido")
            
            logger.info(f"✅ {field_name} validado: {str_value[:20]}...")
            return str_value
            
        except Exception as e:
            if isinstance(e, ValidationError):
                raise
            raise ValidationError(f"❌ Erro ao validar {field_name}: {str(e)}")
    
    @staticmethod
    def validate_email(email: Any, required: bool = False) -> str:
        """Validar email"""
        if not required and (not email or email == ""):
            return ""
        
        if required and (not email or email == ""):
            raise ValidationError("❌ Email é obrigatório")
        
        email_str = str(email).strip().lower()
        
        if not re.match(RobustValidator.PATTERNS['email'], email_str):
            raise ValidationError("❌ Formato de email inválido")
        
        logger.info(f"✅ Email validado: {email_str}")
        return email_str
    
    @staticmethod
    def validate_integer(value: Any, field_name: str, min_value: int = None, 
                        max_value: int = None, required: bool = True) -> int:
        """Validar número inteiro"""
        if not required and (value is None or value == ""):
            return None
        
        if required and (value is None or value == ""):
            raise ValidationError(f"❌ {field_name} é obrigatório")
        
        try:
            int_value = int(value)
        except (ValueError, TypeError):
            raise ValidationError(f"❌ {field_name} deve ser um número inteiro")
        
        if min_value is not None and int_value < min_value:
            raise ValidationError(f"❌ {field_name} deve ser pelo menos {min_value}")
        
        if max_value is not None and int_value > max_value:
            raise ValidationError(f"❌ {field_name} deve ser no máximo {max_value}")
        
        logger.info(f"✅ {field_name} validado: {int_value}")
        return int_value
    
    @staticmethod
    def validate_float(value: Any, field_name: str, min_value: float = None, 
                      max_value: float = None, required: bool = True) -> float:
        """Validar número decimal"""
        if not required and (value is None or value == ""):
            return None
        
        if required and (value is None or value == ""):
            raise ValidationError(f"❌ {field_name} é obrigatório")
        
        try:
            float_value = float(value)
        except (ValueError, TypeError):
            raise ValidationError(f"❌ {field_name} deve ser um número")
        
        if min_value is not None and float_value < min_value:
            raise ValidationError(f"❌ {field_name} deve ser pelo menos {min_value}")
        
        if max_value is not None and float_value > max_value:
            raise ValidationError(f"❌ {field_name} deve ser no máximo {max_value}")
        
        logger.info(f"✅ {field_name} validado: {float_value}")
        return float_value
    
    @staticmethod
    def validate_datetime(value: Any, field_name: str, required: bool = True, 
                         future_only: bool = False) -> datetime:
        """Validar data/hora"""
        if not required and (value is None or value == ""):
            return None
        
        if required and (value is None or value == ""):
            raise ValidationError(f"❌ {field_name} é obrigatório")
        
        # Se já é datetime, validar apenas
        if isinstance(value, datetime):
            dt_value = value
        else:
            # Tentar converter string para datetime
            try:
                if isinstance(value, str):
                    # Formatos comuns aceitos
                    formats = [
                        '%Y-%m-%d %H:%M:%S',
                        '%Y-%m-%d %H:%M',
                        '%Y-%m-%d',
                        '%d/%m/%Y %H:%M:%S',
                        '%d/%m/%Y %H:%M',
                        '%d/%m/%Y'
                    ]
                    
                    dt_value = None
                    for fmt in formats:
                        try:
                            dt_value = datetime.strptime(value, fmt)
                            break
                        except ValueError:
                            continue
                    
                    if dt_value is None:
                        raise ValueError("Formato não reconhecido")
                else:
                    dt_value = datetime.fromisoformat(str(value))
                    
            except (ValueError, TypeError) as e:
                raise ValidationError(f"❌ {field_name} deve ser uma data/hora válida. Erro: {str(e)}")
        
        # Verificar se é futuro se necessário
        if future_only and dt_value <= datetime.now():
            raise ValidationError(f"❌ {field_name} deve ser uma data/hora futura")
        
        logger.info(f"✅ {field_name} validado: {dt_value}")
        return dt_value
    
    @staticmethod
    def validate_status(value: Any, status_type: str) -> str:
        """Validar status baseado no tipo"""
        if not value:
            raise ValidationError(f"❌ Status {status_type} é obrigatório")
        
        status_str = str(value).strip().lower()
        
        valid_statuses = RobustValidator.VALID_STATUS.get(status_type, [])
        if status_str not in valid_statuses:
            raise ValidationError(f"❌ Status inválido. Valores aceitos: {', '.join(valid_statuses)}")
        
        logger.info(f"✅ Status {status_type} validado: {status_str}")
        return status_str
    
    @staticmethod
    def sanitize_sql_input(value: Any) -> str:
        """Sanitizar entrada para prevenir SQL injection"""
        if value is None:
            return ""
        
        # Converter para string e escapar caracteres perigosos
        str_value = str(value)
        
        # Remover caracteres de controle
        str_value = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', str_value)
        
        # Escapar aspas
        str_value = str_value.replace("'", "''").replace('"', '""')
        
        # Remover comentários SQL
        str_value = re.sub(r'--.*$', '', str_value, flags=re.MULTILINE)
        str_value = re.sub(r'/\*.*?\*/', '', str_value, flags=re.DOTALL)
        
        # Limitar tamanho
        if len(str_value) > 1000:
            str_value = str_value[:1000]
            logger.warning(f"⚠️ Entrada truncada para 1000 caracteres")
        
        return str_value.strip()

class DatabaseValidator:
    """Validador para operações de banco de dados"""
    
    @staticmethod
    def validate_query_params(params: Dict[str, Any]) -> Dict[str, Any]:
        """Validar parâmetros de query"""
        validated = {}
        
        for key, value in params.items():
            # Sanitizar todos os valores
            if isinstance(value, str):
                validated[key] = RobustValidator.sanitize_sql_input(value)
            else:
                validated[key] = value
        
        logger.info(f"✅ Parâmetros de query validados: {len(validated)} parâmetros")
        return validated
    
    @staticmethod
    def validate_sql_query(query: str) -> str:
        """Validar query SQL para prevenir operações perigosas"""
        import re
        
        # Lista de padrões proibidos (usando word boundaries para evitar falsos positivos)
        forbidden_patterns = [
            r'\bDROP\b', r'\bDELETE\b', r'\bTRUNCATE\b', r'\bALTER\b', 
            r'\bCREATE\b', r'\bINSERT\b', r'\bUPDATE\b',
            r'\bEXEC\b', r'\bEXECUTE\b', r'\bSCRIPT\b', 
            r'--', r'/\*', r'\*/', r'\bxp_', r'\bsp_'
        ]
        
        query_upper = query.upper()
        
        for pattern in forbidden_patterns:
            if re.search(pattern, query_upper):
                match = re.search(pattern, query_upper)
                raise ValidationError(f"❌ Query contém operação proibida: {match.group()}")
        
        # Limitar tamanho da query
        if len(query) > 5000:
            raise ValidationError("❌ Query muito longa (máximo 5000 caracteres)")
        
        logger.info("✅ Query SQL validada")
        return query
    
    @staticmethod
    def safe_execute_query(engine, query: str, params: Dict[str, Any] = None):
        """Executar query de forma segura com validação"""
        try:
            # Validar query
            validated_query = DatabaseValidator.validate_sql_query(query)
            
            # Validar parâmetros
            validated_params = DatabaseValidator.validate_query_params(params or {})
            
            with engine.connect() as conn:
                if validated_params:
                    result = conn.execute(text(validated_query), validated_params)
                else:
                    result = conn.execute(text(validated_query))
                
                # Retornar dados ao invés do cursor para evitar erro de cursor fechado
                try:
                    # Primeiro tentar scalar para queries simples como COUNT
                    if 'COUNT(' in validated_query.upper():
                        scalar_value = result.scalar()
                        logger.info("✅ Query executada com sucesso")
                        return scalar_value
                    else:
                        # Para queries SELECT complexas
                        data = result.fetchall()
                        logger.info("✅ Query executada com sucesso")
                        return data
                except Exception:
                    # Fallback: tentar fetchall
                    try:
                        data = result.fetchall()
                        logger.info("✅ Query executada com sucesso")
                        return data
                    except Exception:
                        # Se não conseguir buscar dados, retornar resultado simples
                        logger.info("✅ Query executada com sucesso")
                        return result.rowcount
                
        except Exception as e:
            logger.error(f"❌ Erro ao executar query: {str(e)}")
            raise ValidationError(f"Erro na execução da query: {str(e)}")

def validate_user_input(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validar entrada de dados de usuário"""
    validated = {}
    errors = []
    
    try:
        # Nome obrigatório com validação brasileira
        if 'nome' in data:
            validated['nome'] = RobustValidator.validate_string(
                data['nome'], 'Nome', 
                min_length=RobustValidator.LIMITS['name_min'],
                max_length=RobustValidator.LIMITS['name_max'],
                pattern=RobustValidator.PATTERNS['name']
            )
        
        # Telefone obrigatório com validação brasileira
        if 'telefone' in data:
            is_valid, formatted_phone = validate_brazilian_phone(data['telefone'])
            if not is_valid:
                raise ValidationError("❌ Formato de telefone brasileiro inválido")
            validated['telefone'] = format_phone_display(formatted_phone)
            validated['wa_id'] = formatted_phone  # WhatsApp ID é o telefone formatado
        
        # Email opcional
        if 'email' in data:
            validated['email'] = RobustValidator.validate_email(data['email'], required=False)
        
    except ValidationError as e:
        errors.append(str(e))
    
    if errors:
        raise ValidationError("; ".join(errors))
    
    logger.info("✅ Dados de usuário validados com sucesso")
    return validated

def validate_message_input(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validar entrada de dados de mensagem"""
    validated = {}
    errors = []
    
    try:
        # Conteúdo obrigatório
        if 'content' in data:
            validated['content'] = RobustValidator.validate_string(
                data['content'], 'Conteúdo da mensagem',
                min_length=1,
                max_length=RobustValidator.LIMITS['message_max']
            )
        
        # IDs obrigatórios
        for field in ['user_id', 'conversation_id']:
            if field in data:
                validated[field] = RobustValidator.validate_integer(
                    data[field], f'ID {field}',
                    min_value=1
                )
        
        # Direction obrigatória
        if 'direction' in data:
            direction = str(data['direction']).lower()
            if direction not in ['in', 'out']:
                raise ValidationError("❌ Direção deve ser 'in' ou 'out'")
            validated['direction'] = direction
        
    except ValidationError as e:
        errors.append(str(e))
    
    if errors:
        raise ValidationError("; ".join(errors))
    
    logger.info("✅ Dados de mensagem validados com sucesso")
    return validated

def validate_appointment_input(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validar entrada de dados de agendamento"""
    validated = {}
    errors = []
    
    try:
        # Data/hora obrigatória e futura
        if 'date_time' in data:
            validated['date_time'] = RobustValidator.validate_datetime(
                data['date_time'], 'Data/Hora do agendamento',
                future_only=True
            )
        
        # IDs obrigatórios
        for field in ['user_id', 'service_id']:
            if field in data:
                validated[field] = RobustValidator.validate_integer(
                    data[field], f'ID {field}',
                    min_value=1
                )
        
        # Status obrigatório
        if 'status' in data:
            validated['status'] = RobustValidator.validate_status(
                data['status'], 'appointment'
            )
        
        # Notas opcionais
        if 'notes' in data:
            validated['notes'] = RobustValidator.validate_string(
                data['notes'], 'Notas',
                min_length=0,
                max_length=RobustValidator.LIMITS['notes_max'],
                required=False
            )
        
        # Preço opcional
        if 'price' in data and data['price']:
            validated['price'] = RobustValidator.validate_float(
                data['price'], 'Preço',
                min_value=RobustValidator.LIMITS['price_min'],
                max_value=RobustValidator.LIMITS['price_max'],
                required=False
            )
        
    except ValidationError as e:
        errors.append(str(e))
    
    if errors:
        raise ValidationError("; ".join(errors))
    
    logger.info("✅ Dados de agendamento validados com sucesso")
    return validated


def validate_brazilian_phone(phone: str) -> Tuple[bool, str]:
    """
    Valida e formata telefone brasileiro para WhatsApp
    
    Args:
        phone: Número de telefone em qualquer formato
        
    Returns:
        Tuple[bool, str]: (is_valid, formatted_phone)
        
    Examples:
        >>> validate_brazilian_phone("11999999999")
        (True, "5511999999999")
        
        >>> validate_brazilian_phone("5511999999999")
        (True, "5511999999999")
        
        >>> validate_brazilian_phone("+55 11 99999-9999")
        (True, "5511999999999")
        
        >>> validate_brazilian_phone("123456")
        (False, "")
    """
    if not phone:
        return False, ""
    
    # Remover todos os caracteres não numéricos
    clean = re.sub(r'[^\d]', '', phone)
    
    # WhatsApp sempre tem 13 dígitos para Brasil: 5511999999999
    if clean.startswith('55'):
        if len(clean) == 13:
            # Validar DDD
            area_code = clean[2:4]
            if not validate_brazilian_ddd(area_code):
                return False, ""
            
            # Verificar se é um número de celular válido (9 na terceira posição do número local)
            if clean[4] == '9':
                return True, clean
            else:
                return False, ""  # Números fixos não são válidos para WhatsApp
        elif len(clean) == 12:
            # Número fixo brasileiro com código do país - não válido para WhatsApp
            return False, ""
    
    # Adicionar código do país se não tiver
    elif len(clean) == 11:
        # Validar DDD
        area_code = clean[:2]
        if not validate_brazilian_ddd(area_code):
            return False, ""
            
        # Verificar se é celular (com 9)
        if clean[2] == '9':
            return True, f"55{clean}"
        else:
            # Número fixo - não válido para WhatsApp
            return False, ""
    
    # Número com 10 dígitos (fixo sem 9) - não válido para WhatsApp
    elif len(clean) == 10:
        return False, ""
    
    return False, ""


def validate_brazilian_ddd(area_code: str) -> bool:
    """
    Valida código DDD brasileiro
    
    Args:
        area_code: Código de área (DDD)
        
    Returns:
        bool: True se válido
    """
    valid_ddds = {
        # Região Sudeste
        '11', '12', '13', '14', '15', '16', '17', '18', '19',  # São Paulo
        '21', '22', '24',  # Rio de Janeiro
        '27', '28',  # Espírito Santo
        '31', '32', '33', '34', '35', '37', '38',  # Minas Gerais
        
        # Região Sul
        '41', '42', '43', '44', '45', '46',  # Paraná
        '47', '48', '49',  # Santa Catarina
        '51', '53', '54', '55',  # Rio Grande do Sul
        
        # Região Nordeste
        '71', '73', '74', '75', '77',  # Bahia
        '79',  # Sergipe
        '81', '87',  # Pernambuco
        '82',  # Alagoas
        '83',  # Paraíba
        '84',  # Rio Grande do Norte
        '85', '88',  # Ceará
        '86', '89',  # Piauí
        '98', '99',  # Maranhão
        
        # Região Norte
        '61',  # Distrito Federal e Goiás (parte)
        '62', '64',  # Goiás
        '63',  # Tocantins
        '65', '66',  # Mato Grosso
        '67',  # Mato Grosso do Sul
        '68',  # Acre
        '69',  # Rondônia
        '91', '93', '94',  # Pará
        '92', '97',  # Amazonas
        '95',  # Roraima
        '96',  # Amapá
    }
    
    return area_code in valid_ddds


def format_phone_display(phone: str) -> str:
    """
    Formata telefone para exibição amigável
    
    Args:
        phone: Telefone no formato 5511999999999
        
    Returns:
        str: Telefone formatado para exibição
        
    Example:
        >>> format_phone_display("5511999999999")
        "+55 (11) 99999-9999"
    """
    if not phone or len(phone) != 13:
        return phone
    
    if phone.startswith('55'):
        country = phone[:2]
        area = phone[2:4]
        first_part = phone[4:9]
        second_part = phone[9:]
        
        return f"+{country} ({area}) {first_part}-{second_part}"
    
    return phone


def extract_phone_from_text(text: str) -> str:
    """
    Extrai número de telefone de um texto
    
    Args:
        text: Texto contendo possível número de telefone
        
    Returns:
        str: Número extraído e formatado ou string vazia
    """
    # Padrões comuns de telefone brasileiro
    patterns = [
        r'\+55\s*\(?(\d{2})\)?\s*9?\d{4}[-\s]?\d{4}',  # +55 (11) 99999-9999
        r'55\s*\(?(\d{2})\)?\s*9?\d{4}[-\s]?\d{4}',    # 55 (11) 99999-9999
        r'\(?(\d{2})\)?\s*9?\d{4}[-\s]?\d{4}',         # (11) 99999-9999
        r'(\d{2})\s*9?\d{4}[-\s]?\d{4}',               # 11 99999-9999
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            # Extrair todos os dígitos
            phone_numbers = re.findall(r'\d+', match.group())
            if phone_numbers:
                phone = ''.join(phone_numbers)
                is_valid, formatted = validate_brazilian_phone(phone)
                if is_valid:
                    return formatted
    
    return ""


def normalize_phone_input(phone: str) -> str:
    """
    Normaliza entrada de telefone removendo caracteres especiais
    
    Args:
        phone: Telefone em qualquer formato
        
    Returns:
        str: Telefone apenas com dígitos
    """
    if not phone:
        return ""
    
    # Remover todos os caracteres não numéricos
    return re.sub(r'[^\d]', '', phone)


def is_whatsapp_phone(phone: str) -> bool:
    """
    Verifica se o telefone está no formato válido para WhatsApp
    
    Args:
        phone: Telefone para verificar
        
    Returns:
        bool: True se está no formato WhatsApp (13 dígitos começando com 55, apenas números)
    """
    if not phone:
        return False
    
    # Deve ser apenas dígitos, sem símbolos
    if not phone.isdigit():
        return False
    
    return len(phone) == 13 and phone.startswith('55')


# Aliases para compatibilidade
validate_phone = validate_brazilian_phone
format_phone = format_phone_display
