#!/usr/bin/env python3
"""
🔍 ANALISADOR DE BANCO - FUNCIONAL
"""

import asyncio
import asyncpg
import json
from datetime import datetime

DATABASE_URL = "postgresql://postgres:UGARTPCwAADBBeBLctoRnQXLsoUvLJxz@caboose.proxy.rlwy.net:13910/railway"

async def main():
    print("🚀 Analisando banco de dados...")
    
    try:
        db = await asyncpg.connect(DATABASE_URL)
        print("✅ Conectado!")
        
        # Lista tabelas
        tables = await db.fetch("""
            SELECT table_name, 
                   pg_size_pretty(pg_total_relation_size(c.oid)) as size
            FROM information_schema.tables t
            LEFT JOIN pg_class c ON c.relname = t.table_name
            WHERE t.table_schema = 'public'
            ORDER BY t.table_name
        """)
        
        print(f"\n📊 {len(tables)} tabelas encontradas:")
        
        report = {}
        
        for table in tables:
            table_name = table['table_name']
            print(f"  🔍 {table_name} ({table['size']})")
            
            # Colunas
            columns = await db.fetch("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_name = $1 AND table_schema = 'public'
                ORDER BY ordinal_position
            """, table_name)
            
            # Count
            try:
                count = await db.fetchval(f"SELECT COUNT(*) FROM {table_name}")
            except:
                count = 0
                
            report[table_name] = {
                'size': table['size'],
                'rows': count,
                'columns': [dict(c) for c in columns]
            }
            
            print(f"    📄 {len(columns)} colunas, {count} registros")
            
            # Check specific issues
            if table_name == 'conversations':
                has_context = any(c['column_name'] == 'context' for c in columns)
                print(f"    {'✅' if has_context else '❌'} Coluna 'context': {has_context}")
        
        # Save report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"database_report_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2, default=str)
            
        await db.close()
        
        print(f"\n✅ Análise concluída!")
        print(f"📄 Relatório salvo: {filename}")
        
        return filename
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        return None

if __name__ == "__main__":
    asyncio.run(main())
