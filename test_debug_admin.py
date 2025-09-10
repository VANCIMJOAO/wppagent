#!/usr/bin/env python3
"""
🔍 Debug Admin User - Railway PostgreSQL Test
==============================================
Simple test to debug admin user authentication issues
"""

import os
import asyncpg
import asyncio
from datetime import datetime
from passlib.context import CryptContext
import uuid

# Setup password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Railway PostgreSQL connection
DATABASE_URL = "postgresql://postgres:UGARTPCwAADBBeBLctoRnQXLsoUvLJxz@caboose.proxy.rlwy.net:13910/railway"

async def test_admin_debug():
    """Test admin user creation and verification"""
    
    # Generate unique test username
    test_id = str(uuid.uuid4())[:8]
    test_username = f"debug_admin_{test_id}"
    test_password = "test123456"
    test_email = f"{test_username}@test.com"
    
    connection = None
    try:
        # Connect to Railway PostgreSQL
        print("🔗 Connecting to Railway PostgreSQL...")
        connection = await asyncpg.connect(DATABASE_URL)
        print("✅ Connected successfully")
        
        # Hash password
        password_hash = pwd_context.hash(test_password)
        print(f"🔐 Password hashed: {password_hash[:20]}...")
        
        # Create test admin user
        print(f"👤 Creating test admin user: {test_username}")
        await connection.execute("""
            INSERT INTO admin_users (
                username, email, password_hash, full_name,
                is_active, is_super_admin, created_at, updated_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        """, 
            test_username,
            test_email, 
            password_hash,
            f"Debug Test Admin {test_id}",
            True,
            False,
            datetime.utcnow(),
            datetime.utcnow()
        )
        print("✅ Test admin user created")
        
        # Verify user exists in database
        user_record = await connection.fetchrow(
            "SELECT username, email, is_active, password_hash FROM admin_users WHERE username = $1",
            test_username
        )
        
        if user_record:
            print("✅ User found in database:")
            print(f"   Username: {user_record['username']}")
            print(f"   Email: {user_record['email']}")
            print(f"   Active: {user_record['is_active']}")
            print(f"   Hash exists: {bool(user_record['password_hash'])}")
            print(f"   Hash preview: {user_record['password_hash'][:20]}...")
            
            # Test password verification
            stored_hash = user_record['password_hash']
            password_verified = pwd_context.verify(test_password, stored_hash)
            print(f"   Password verified: {password_verified}")
            
        else:
            print("❌ User not found in database")
        
        # Test direct API call to debug endpoint
        print("\n🌐 Testing FastAPI debug endpoint...")
        from fastapi.testclient import TestClient
        from app.main import app
        
        with TestClient(app) as client:
            debug_response = client.post("/admin/debug-admin", json={
                "username": test_username,
                "password": test_password
            })
            
            print(f"Debug endpoint status: {debug_response.status_code}")
            print(f"Debug endpoint response: {debug_response.json()}")
        
        # Cleanup
        await connection.execute(
            "DELETE FROM admin_users WHERE username = $1",
            test_username
        )
        print(f"🧹 Cleaned up test user: {test_username}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if connection:
            await connection.close()
            print("🔗 Database connection closed")

if __name__ == "__main__":
    asyncio.run(test_admin_debug())