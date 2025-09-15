#!/usr/bin/env python3
"""
Test database connection with the provided PostgreSQL URL
"""

import os
import asyncpg
import asyncio
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

async def test_db_connection():
    """Test the database connection"""
    database_url = os.getenv("DATABASE_URL")
    
    if not database_url:
        print("❌ DATABASE_URL environment variable not set")
        return False
    
    print(f"🔍 Testing connection to: {database_url}")
    
    try:
        # Try to connect using asyncpg directly
        conn = await asyncpg.connect(database_url)
        
        # Test a simple query
        version = await conn.fetchval("SELECT version()")
        print(f"✅ Connection successful!")
        print(f"📊 PostgreSQL version: {version[:50]}...")
        
        await conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_db_connection())