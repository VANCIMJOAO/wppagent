#!/usr/bin/env python3
"""
🔧 Script para corrigir todas as dependencies dos endpoints de analytics
"""

import re

def fix_analytics_file():
    file_path = "/home/vancim/whats_agent/app/routes/analytics.py"
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Corrigir todas as ocorrências de current_admin para current_user
    content = re.sub(
        r'current_admin: AdminUser = Depends\(get_current_admin_user\)',
        'current_user: dict = Depends(get_current_user)',
        content
    )
    
    # Corrigir referencias nos logs
    content = re.sub(
        r'current_admin\.username',
        'current_user[\'user_id\']',
        content
    )
    
    # Corrigir imports desnecessários
    content = re.sub(
        r'from app\.routes\.admin_auth import get_current_admin_user\n',
        '',
        content
    )
    
    with open(file_path, 'w') as f:
        f.write(content)
    
    print("✅ Analytics.py corrigido!")

if __name__ == "__main__":
    fix_analytics_file()
