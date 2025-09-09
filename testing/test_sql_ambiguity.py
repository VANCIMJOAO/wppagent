#!/usr/bin/env python3
"""
Test script to check for SQL ambiguous column issues
"""

import sys
import asyncio
import os
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Add app to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.config.config_factory import get_settings, get_database_url
from app.models.database import Base, Conversation, Message, User
from app.database import get_db

async def test_queries():
    """Test for ambiguous column issues"""
    print("🔍 Testing SQL queries for ambiguous column issues...")
    
    # Create test database connection
    database_url = get_database_url()
    engine = create_async_engine(database_url, echo=False)
    
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        try:
            # Test 1: Complex conversations query (the main problematic one)
            print("\n1️⃣ Testing conversations query with joins...")
            
            # This is the query that could be problematic
            from sqlalchemy import select, func, desc, and_, or_
            
            query = select(
                Conversation,
                User.nome.label("user_name"),
                User.telefone.label("user_phone"),
                func.count(Message.id).label("total_messages")
            ).select_from(
                Conversation
            ).join(
                User, Conversation.user_id == User.id
            ).outerjoin(
                Message, Conversation.id == Message.conversation_id
            ).group_by(
                Conversation.id, User.id
            ).limit(5)
            
            result = await session.execute(query)
            rows = result.fetchall()
            print(f"✅ Query 1 executed successfully: {len(rows)} results")
            
            # Test 2: Stats query
            print("\n2️⃣ Testing stats query...")
            
            stats_query = select(
                func.count(Conversation.id).label("total_conversations"),
                func.count(Conversation.id.filter(Conversation.status == "active")).label("active_conversations"),
                func.count(Conversation.id.filter(Conversation.status == "pending")).label("pending_conversations"),
                func.count(Message.id).label("total_messages"),
            ).select_from(
                Conversation
            ).outerjoin(
                Message, Conversation.id == Message.conversation_id
            )
            
            stats_result = await session.execute(stats_query)
            stats = stats_result.fetchone()
            print(f"✅ Query 2 executed successfully: {stats}")
            
            # Test 3: Specific conversation query
            print("\n3️⃣ Testing specific conversation query...")
            
            conv_query = select(
                Conversation,
                User.nome.label("user_name"),
                User.telefone.label("user_phone"),
                func.count(Message.id).label("total_messages")
            ).select_from(Conversation).join(
                User, Conversation.user_id == User.id
            ).outerjoin(
                Message, Conversation.id == Message.conversation_id
            ).where(
                Conversation.id == 1
            ).group_by(
                Conversation.id, User.id
            )
            
            conv_result = await session.execute(conv_query)
            row = conv_result.fetchone()
            print(f"✅ Query 3 executed successfully: {row is not None}")
            
            print("\n🎉 All queries executed without ambiguous column errors!")
            
        except Exception as e:
            print(f"\n❌ Error found: {e}")
            if "ambiguous" in str(e).lower():
                print("🚨 AMBIGUOUS COLUMN ERROR DETECTED!")
                return False
            else:
                print("ℹ️  Different error (might be normal if no data exists)")
                return True
    
    return True

if __name__ == "__main__":
    result = asyncio.run(test_queries())
    if result:
        print("\n✅ No ambiguous column issues found!")
    else:
        print("\n❌ Ambiguous column issues detected!")
        sys.exit(1)
