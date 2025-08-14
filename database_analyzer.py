#!/usr/bin/env python3
"""
📊 ANALISADOR DE DATABASE - WhatsApp Agent
==========================================
Gera relatório completo do esquema e dados da database
"""

import asyncio
import asyncpg
import json
from datetime import datetime, timedelta
import sys

class DatabaseAnalyzer:
    def __init__(self):
        self.DATABASE_URL = "postgresql://postgres:UGARTPCwAADBBeBLctoRnQXLsoUvLJxz@caboose.proxy.rlwy.net:13910/railway"
        self.db = None
        self.report = {
            "timestamp": datetime.now().isoformat(),
            "database_info": {},
            "schema_analysis": {},
            "tables": {},
            "relationships": [],
            "data_summary": {},
            "sample_data": {},
            "statistics": {}
        }

    async def connect(self):
        """Conecta ao banco"""
        try:
            self.db = await asyncpg.connect(self.DATABASE_URL)
            print("✅ Conectado ao PostgreSQL")
            return True
        except Exception as e:
            print(f"❌ Erro de conexão: {e}")
            return False

    async def analyze_database_info(self):
        """Informações básicas da database"""
        print("📊 Analisando informações da database...")
        
        # Versão do PostgreSQL
        version = await self.db.fetchval("SELECT version()")
        
        # Database atual
        current_db = await self.db.fetchval("SELECT current_database()")
        
        # Timezone
        timezone = await self.db.fetchval("SHOW timezone")
        
        self.report["database_info"] = {
            "postgresql_version": version,
            "current_database": current_db,
            "timezone": timezone
        }

    async def analyze_schema(self):
        """Analisa o esquema completo"""
        print("🏗️  Analisando esquema...")
        
        # Listar todas as tabelas
        tables = await self.db.fetch("""
            SELECT table_name, table_type
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        
        # Listar índices
        indexes = await self.db.fetch("""
            SELECT 
                schemaname, tablename, indexname, indexdef
            FROM pg_indexes
            WHERE schemaname = 'public'
            ORDER BY tablename, indexname
        """)
        
        # Listar constraints
        constraints = await self.db.fetch("""
            SELECT 
                tc.table_name,
                tc.constraint_name,
                tc.constraint_type,
                kcu.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu 
                ON tc.constraint_name = kcu.constraint_name
            WHERE tc.table_schema = 'public'
            ORDER BY tc.table_name, tc.constraint_type
        """)
        
        self.report["schema_analysis"] = {
            "total_tables": len(tables),
            "table_list": [{"name": t["table_name"], "type": t["table_type"]} for t in tables],
            "total_indexes": len(indexes),
            "indexes": [{"table": i["tablename"], "name": i["indexname"], "definition": i["indexdef"]} for i in indexes],
            "constraints": [{"table": c["table_name"], "name": c["constraint_name"], "type": c["constraint_type"], "column": c["column_name"]} for c in constraints]
        }

    async def analyze_table_structure(self):
        """Analisa estrutura de cada tabela"""
        print("📋 Analisando estrutura das tabelas...")
        
        tables = await self.db.fetch("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """)
        
        for table in tables:
            table_name = table["table_name"]
            print(f"  📄 Analisando tabela: {table_name}")
            
            # Estrutura das colunas
            columns = await self.db.fetch(f"""
                SELECT 
                    column_name,
                    data_type,
                    is_nullable,
                    column_default,
                    character_maximum_length
                FROM information_schema.columns
                WHERE table_name = '{table_name}' AND table_schema = 'public'
                ORDER BY ordinal_position
            """)
            
            # Contagem de registros
            try:
                count = await self.db.fetchval(f"SELECT COUNT(*) FROM {table_name}")
            except:
                count = 0
            
            # Tamanho da tabela
            try:
                size_info = await self.db.fetchrow(f"""
                    SELECT 
                        pg_size_pretty(pg_total_relation_size('{table_name}')) as total_size,
                        pg_size_pretty(pg_relation_size('{table_name}')) as table_size
                """)
                size = {
                    "total_size": size_info["total_size"],
                    "table_size": size_info["table_size"]
                }
            except:
                size = {"total_size": "N/A", "table_size": "N/A"}
            
            self.report["tables"][table_name] = {
                "columns": [
                    {
                        "name": col["column_name"],
                        "type": col["data_type"],
                        "nullable": col["is_nullable"] == "YES",
                        "default": col["column_default"],
                        "max_length": col["character_maximum_length"]
                    }
                    for col in columns
                ],
                "row_count": count,
                "size": size
            }

    async def analyze_relationships(self):
        """Analisa relacionamentos entre tabelas"""
        print("🔗 Analisando relacionamentos...")
        
        foreign_keys = await self.db.fetch("""
            SELECT
                kcu.table_name as source_table,
                kcu.column_name as source_column,
                ccu.table_name AS target_table,
                ccu.column_name AS target_column,
                tc.constraint_name
            FROM information_schema.table_constraints AS tc 
            JOIN information_schema.key_column_usage AS kcu
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage AS ccu
                ON ccu.constraint_name = tc.constraint_name
                AND ccu.table_schema = tc.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY'
            AND tc.table_schema = 'public'
        """)
        
        self.report["relationships"] = [
            {
                "source_table": fk["source_table"],
                "source_column": fk["source_column"],
                "target_table": fk["target_table"],
                "target_column": fk["target_column"],
                "constraint_name": fk["constraint_name"]
            }
            for fk in foreign_keys
        ]

    async def collect_sample_data(self):
        """Coleta dados de exemplo"""
        print("📝 Coletando dados de exemplo...")
        
        tables = list(self.report["tables"].keys())
        
        for table_name in tables:
            if self.report["tables"][table_name]["row_count"] > 0:
                print(f"  📄 Coletando samples de: {table_name}")
                
                try:
                    # Primeiros 3 registros
                    samples = await self.db.fetch(f"SELECT * FROM {table_name} LIMIT 3")
                    
                    self.report["sample_data"][table_name] = [
                        {key: str(value) if value is not None else None for key, value in dict(sample).items()}
                        for sample in samples
                    ]
                except Exception as e:
                    self.report["sample_data"][table_name] = f"Erro ao coletar: {e}"

    async def analyze_whatsapp_specific_data(self):
        """Análise específica para dados do WhatsApp"""
        print("📱 Analisando dados específicos do WhatsApp...")
        
        whatsapp_stats = {}
        
        # Análise de usuários
        try:
            users_data = await self.db.fetch("""
                SELECT 
                    COUNT(*) as total_users,
                    COUNT(CASE WHEN phone_number IS NOT NULL THEN 1 END) as users_with_phone
                FROM users
            """)
            whatsapp_stats["users"] = dict(users_data[0]) if users_data else {}
        except Exception as e:
            whatsapp_stats["users"] = f"Erro: {e}"
        
        # Análise de conversas
        try:
            conversations_data = await self.db.fetch("""
                SELECT 
                    COUNT(*) as total_conversations,
                    COUNT(CASE WHEN status = 'active' THEN 1 END) as active_conversations,
                    COUNT(CASE WHEN status = 'human' THEN 1 END) as human_conversations
                FROM conversations
            """)
            whatsapp_stats["conversations"] = dict(conversations_data[0]) if conversations_data else {}
        except Exception as e:
            whatsapp_stats["conversations"] = f"Erro: {e}"
        
        # Análise de mensagens
        try:
            messages_data = await self.db.fetch("""
                SELECT 
                    COUNT(*) as total_messages,
                    COUNT(CASE WHEN direction = 'in' THEN 1 END) as incoming_messages,
                    COUNT(CASE WHEN direction = 'out' THEN 1 END) as outgoing_messages,
                    COUNT(CASE WHEN message_type = 'text' THEN 1 END) as text_messages,
                    AVG(LENGTH(content)) as avg_message_length
                FROM messages
            """)
            whatsapp_stats["messages"] = dict(messages_data[0]) if messages_data else {}
        except Exception as e:
            whatsapp_stats["messages"] = f"Erro: {e}"
        
        # Mensagens por período (últimas 24h)
        try:
            recent_messages = await self.db.fetch("""
                SELECT 
                    DATE_TRUNC('hour', created_at) as hour,
                    COUNT(*) as message_count,
                    COUNT(CASE WHEN direction = 'in' THEN 1 END) as incoming,
                    COUNT(CASE WHEN direction = 'out' THEN 1 END) as outgoing
                FROM messages
                WHERE created_at > NOW() - INTERVAL '24 hours'
                GROUP BY DATE_TRUNC('hour', created_at)
                ORDER BY hour
            """)
            whatsapp_stats["recent_activity"] = [
                {
                    "hour": msg["hour"].isoformat(),
                    "total": msg["message_count"],
                    "incoming": msg["incoming"],
                    "outgoing": msg["outgoing"]
                }
                for msg in recent_messages
            ]
        except Exception as e:
            whatsapp_stats["recent_activity"] = f"Erro: {e}"
        
        # Top usuários por mensagens
        try:
            top_users = await self.db.fetch("""
                SELECT 
                    u.phone_number,
                    u.name,
                    COUNT(m.id) as message_count,
                    MAX(m.created_at) as last_message
                FROM users u
                LEFT JOIN conversations c ON u.id = c.user_id
                LEFT JOIN messages m ON c.id = m.conversation_id
                GROUP BY u.id, u.phone_number, u.name
                HAVING COUNT(m.id) > 0
                ORDER BY message_count DESC
                LIMIT 5
            """)
            whatsapp_stats["top_users"] = [
                {
                    "phone": user["phone_number"],
                    "name": user["name"],
                    "message_count": user["message_count"],
                    "last_message": user["last_message"].isoformat() if user["last_message"] else None
                }
                for user in top_users
            ]
        except Exception as e:
            whatsapp_stats["top_users"] = f"Erro: {e}"
        
        self.report["whatsapp_analysis"] = whatsapp_stats

    async def generate_report(self):
        """Gera o relatório completo"""
        print("📊 Gerando relatório completo...")
        
        await self.analyze_database_info()
        await self.analyze_schema()
        await self.analyze_table_structure()
        await self.analyze_relationships()
        await self.collect_sample_data()
        await self.analyze_whatsapp_specific_data()
        
        # Estatísticas gerais
        self.report["statistics"] = {
            "total_tables": len(self.report["tables"]),
            "total_relationships": len(self.report["relationships"]),
            "total_rows": sum(table["row_count"] for table in self.report["tables"].values()),
            "analysis_timestamp": datetime.now().isoformat()
        }

    async def save_report(self):
        """Salva o relatório"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"database_analysis_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.report, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"📄 Relatório salvo: {filename}")
        return filename

    async def print_summary(self):
        """Imprime resumo na tela"""
        print("\n" + "="*80)
        print("📊 RELATÓRIO DE ANÁLISE DA DATABASE")
        print("="*80)
        
        print(f"🗄️  Database: {self.report['database_info']['current_database']}")
        print(f"⏰ Análise: {self.report['timestamp']}")
        print(f"📋 Total de tabelas: {self.report['statistics']['total_tables']}")
        print(f"📊 Total de registros: {self.report['statistics']['total_rows']}")
        print(f"🔗 Relacionamentos: {self.report['statistics']['total_relationships']}")
        
        print(f"\n📋 TABELAS ENCONTRADAS:")
        print("-" * 50)
        for table_name, table_info in self.report["tables"].items():
            print(f"  📄 {table_name:20} | {table_info['row_count']:>8} registros | {len(table_info['columns'])} colunas")
        
        if "whatsapp_analysis" in self.report:
            print(f"\n📱 ANÁLISE WHATSAPP:")
            print("-" * 50)
            wa = self.report["whatsapp_analysis"]
            
            if isinstance(wa.get("users"), dict):
                print(f"  👥 Usuários: {wa['users'].get('total_users', 'N/A')}")
            
            if isinstance(wa.get("conversations"), dict):
                conv = wa["conversations"]
                print(f"  💬 Conversas: {conv.get('total_conversations', 'N/A')} total, {conv.get('active_conversations', 'N/A')} ativas")
            
            if isinstance(wa.get("messages"), dict):
                msg = wa["messages"]
                print(f"  📨 Mensagens: {msg.get('total_messages', 'N/A')} total")
                print(f"       ↳ Entrada: {msg.get('incoming_messages', 'N/A')}")
                print(f"       ↳ Saída: {msg.get('outgoing_messages', 'N/A')}")
                if msg.get('avg_message_length'):
                    print(f"       ↳ Tamanho médio: {float(msg['avg_message_length']):.1f} caracteres")
        
        print("\n" + "="*80)

    async def close(self):
        """Fecha conexão"""
        if self.db:
            await self.db.close()
            print("✅ Conexão fechada")

async def main():
    analyzer = DatabaseAnalyzer()
    
    try:
        if not await analyzer.connect():
            return
        
        print("🔍 Iniciando análise completa da database...")
        await analyzer.generate_report()
        
        filename = await analyzer.save_report()
        await analyzer.print_summary()
        
        print(f"\n✅ Análise concluída! Relatório detalhado salvo em: {filename}")
        
    except Exception as e:
        print(f"❌ Erro durante análise: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await analyzer.close()

if __name__ == "__main__":
    print("📊 ANALISADOR DE DATABASE - WhatsApp Agent")
    print("=" * 60)
    print("🔍 Analisando esquema completo da database...")
    print("📊 Gerando relatório detalhado...")
    print("=" * 60)
    
    asyncio.run(main())
