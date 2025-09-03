"""
Serviço de Database
==================

Classe para conectar e executar queries na database PostgreSQL do Railway.
Usa a mesma estrutura do backend principal do projeto.
"""

import os
import psycopg2
import psycopg2.extras
from typing import List, Dict, Any, Optional

class DatabaseService:
    def __init__(self):
        """Inicializa conexão com database"""
        self.database_url = os.getenv('DATABASE_URL')
        if not self.database_url:
            raise ValueError("DATABASE_URL não encontrada nas variáveis de ambiente")
        
        # Configura SSL se necessário (Railway requer SSL)
        if 'railway' in self.database_url:
            self.connection_params = {
                'dsn': self.database_url,
                'sslmode': 'require'
            }
        else:
            self.connection_params = {'dsn': self.database_url}
    
    def get_connection(self):
        """Obtém conexão com a database"""
        try:
            conn = psycopg2.connect(**self.connection_params)
            return conn
        except Exception as e:
            print(f"Erro ao conectar com database: {e}")
            raise
    
    def execute_query(self, query: str, params: tuple = None) -> List[Dict[str, Any]]:
        """
        Executa query e retorna resultados como lista de dicionários
        
        Args:
            query (str): Query SQL para executar
            params (tuple): Parâmetros para a query
            
        Returns:
            List[Dict[str, Any]]: Resultados da query
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                    cursor.execute(query, params)
                    
                    # Se é uma query SELECT, retorna os resultados
                    if query.strip().upper().startswith('SELECT'):
                        results = cursor.fetchall()
                        return [dict(row) for row in results]
                    else:
                        # Para INSERT, UPDATE, DELETE
                        conn.commit()
                        return [{"affected_rows": cursor.rowcount}]
                        
        except Exception as e:
            print(f"Erro ao executar query: {e}")
            print(f"Query: {query}")
            print(f"Params: {params}")
            raise
    
    def execute_single(self, query: str, params: tuple = None) -> Optional[Dict[str, Any]]:
        """
        Executa query e retorna apenas o primeiro resultado
        
        Args:
            query (str): Query SQL para executar
            params (tuple): Parâmetros para a query
            
        Returns:
            Optional[Dict[str, Any]]: Primeiro resultado ou None
        """
        results = self.execute_query(query, params)
        return results[0] if results else None
    
    def test_connection(self) -> bool:
        """
        Testa se a conexão com a database está funcionando
        
        Returns:
            bool: True se conectou com sucesso
        """
        try:
            result = self.execute_query("SELECT 1 as test")
            return len(result) == 1 and result[0]['test'] == 1
        except Exception as e:
            print(f"Erro no teste de conexão: {e}")
            return False
    
    def get_company_info(self) -> Optional[Dict[str, Any]]:
        """
        Obtém informações da empresa
        
        Returns:
            Optional[Dict[str, Any]]: Dados da empresa ou None
        """
        query = """
        SELECT 
            company_name,
            slogan,
            about_us,
            business_description,
            whatsapp_number,
            phone_secondary,
            email_contact,
            website,
            street_address,
            city,
            state,
            zip_code,
            country,
            instagram,
            facebook,
            linkedin,
            welcome_message,
            auto_response_enabled,
            created_at,
            updated_at
        FROM company_info 
        WHERE business_id = 1
        ORDER BY created_at DESC 
        LIMIT 1
        """
        return self.execute_single(query)
    
    def get_bot_configurations(self) -> Optional[Dict[str, Any]]:
        """
        Obtém configurações do bot
        
        Returns:
            Optional[Dict[str, Any]]: Configurações do bot ou None
        """
        query = """
        SELECT 
            auto_response_enabled,
            response_delay_min,
            response_delay_max,
            max_retries,
            language,
            timezone,
            max_message_length,
            working_hours_only,
            weekend_support,
            appointment_enabled,
            enable_human_handoff,
            data_collection_enabled,
            required_fields,
            optional_fields,
            created_at,
            updated_at
        FROM bot_configurations 
        WHERE business_id = 1
        ORDER BY created_at DESC 
        LIMIT 1
        """
        return self.execute_single(query)
    
    def get_business_hours(self) -> List[Dict[str, Any]]:
        """
        Obtém horários de funcionamento
        
        Returns:
            List[Dict[str, Any]]: Horários por dia da semana
        """
        query = """
        SELECT 
            day_of_week,
            is_open,
            open_time,
            close_time,
            break_start_time,
            break_end_time,
            notes
        FROM business_hours 
        WHERE business_id = 1
        ORDER BY day_of_week
        """
        return self.execute_query(query)
    
    def get_message_templates(self) -> List[Dict[str, Any]]:
        """
        Obtém templates de mensagens
        
        Returns:
            List[Dict[str, Any]]: Templates de mensagens
        """
        query = """
        SELECT 
            template_key,
            template_name,
            template_content,
            available_variables,
            is_active,
            category
        FROM message_templates 
        WHERE business_id = 1
        ORDER BY category, template_name
        """
        return self.execute_query(query)
    
    def get_business_policies(self) -> List[Dict[str, Any]]:
        """
        Obtém políticas do negócio
        
        Returns:
            List[Dict[str, Any]]: Políticas do negócio
        """
        query = """
        SELECT 
            policy_type,
            title,
            description,
            rules,
            is_active
        FROM business_policies 
        WHERE business_id = 1
        ORDER BY policy_type
        """
        return self.execute_query(query)

# Função de conveniência para uso rápido
def get_db_service() -> DatabaseService:
    """
    Função de conveniência para obter instância do DatabaseService
    
    Returns:
        DatabaseService: Instância do serviço de database
    """
    return DatabaseService()
