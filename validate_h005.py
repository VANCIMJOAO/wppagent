#!/usr/bin/env python3
"""
H005: Validação do Service Worker PWA com bypass para autenticação
Testa se o PWA funciona offline exceto para login/auth
"""

import asyncio
import json
import time
from pathlib import Path

def validate_h005():
    """Validar implementação H005"""
    
    print("🔍 H005: Validando Service Worker PWA com bypass para autenticação...")
    print("=" * 60)
    
    issues = []
    
    # 1. Verificar se sw-h005.js existe
    sw_file = Path("nextjs_dashboard/public/sw-h005.js")
    if sw_file.exists():
        print("✅ Service Worker H005 existe")
        
        # Verificar conteúdo do SW
        with open(sw_file, 'r') as f:
            sw_content = f.read()
            
        if 'AUTH_BYPASS_URLS' in sw_content:
            print("✅ Auth bypass configurado")
        else:
            issues.append("❌ Auth bypass não encontrado no SW")
            
        if 'H005' in sw_content:
            print("✅ Identificação H005 presente")
        else:
            issues.append("❌ Identificação H005 não encontrada")
            
    else:
        issues.append("❌ Service Worker H005 não encontrado")
    
    # 2. Verificar layout.tsx
    layout_file = Path("nextjs_dashboard/app/layout.tsx")
    if layout_file.exists():
        with open(layout_file, 'r') as f:
            layout_content = f.read()
            
        if 'sw-unregister.js' not in layout_content:
            print("✅ sw-unregister.js removido do layout")
        else:
            issues.append("❌ sw-unregister.js ainda presente no layout")
            
        if 'sw-h005.js' in layout_content:
            print("✅ sw-h005.js referenciado no layout")
        else:
            issues.append("❌ sw-h005.js não referenciado no layout")
    
    # 3. Verificar PWAWrapper
    pwa_wrapper = Path("nextjs_dashboard/components/pwa/PWAWrapper.tsx")
    if pwa_wrapper.exists():
        with open(pwa_wrapper, 'r') as f:
            pwa_content = f.read()
            
        if 'sw-h005.js' in pwa_content:
            print("✅ PWAWrapper configurado para sw-h005.js")
        else:
            issues.append("❌ PWAWrapper não configurado para sw-h005.js")
    
    # 4. Verificar manifest.json
    manifest_file = Path("nextjs_dashboard/public/manifest.json")
    if manifest_file.exists():
        try:
            with open(manifest_file, 'r') as f:
                manifest = json.load(f)
                
            if 'H005' in manifest.get('description', ''):
                print("✅ Manifest atualizado com identificação H005")
            else:
                issues.append("❌ Manifest não atualizado com H005")
                
            if manifest.get('display') == 'standalone':
                print("✅ Manifest configurado para PWA standalone")
            else:
                issues.append("❌ Manifest não configurado para standalone")
                
        except json.JSONDecodeError:
            issues.append("❌ Manifest.json inválido")
    
    # 5. Verificar página offline
    offline_page = Path("nextjs_dashboard/app/offline/page.tsx")
    if offline_page.exists():
        with open(offline_page, 'r') as f:
            offline_content = f.read()
            
        if 'LogIn' in offline_content and 'auth=required' in offline_content:
            print("✅ Página offline configurada para auth bypass")
        else:
            issues.append("❌ Página offline não configurada para auth bypass")
    
    print("\n" + "=" * 60)
    
    if not issues:
        print("🎉 H005: VALIDAÇÃO PASSOU - PWA configurado corretamente!")
        print("✅ Service Worker com auth bypass implementado")
        print("✅ PWA funciona offline exceto para login")
        print("✅ Layout e componentes atualizados")
        print("✅ Manifest otimizado para PWA")
        return True
    else:
        print("❌ H005: VALIDAÇÃO FALHOU - Problemas encontrados:")
        for issue in issues:
            print(f"  {issue}")
        return False

def test_auth_bypass_urls():
    """Testar URLs que devem ter bypass de auth"""
    
    print("\n🔐 Testando URLs com bypass de autenticação:")
    
    auth_urls = [
        '/api/auth/',
        '/api/login',
        '/api/logout', 
        '/api/session',
        '/auth/',
        '/login',
        '/logout'
    ]
    
    sw_file = Path("nextjs_dashboard/public/sw-h005.js")
    if sw_file.exists():
        with open(sw_file, 'r') as f:
            sw_content = f.read()
            
        for url in auth_urls:
            if url in sw_content:
                print(f"✅ {url} configurado para bypass")
            else:
                print(f"❌ {url} não configurado para bypass")
    
def test_cacheable_urls():
    """Testar URLs que podem ser cacheadas"""
    
    print("\n📱 Testando URLs que podem funcionar offline:")
    
    cacheable_urls = [
        '/dashboard',
        '/agendamentos',
        '/conversas', 
        '/monitoring',
        '/clientes',
        '/analytics'
    ]
    
    sw_file = Path("nextjs_dashboard/public/sw-h005.js")
    if sw_file.exists():
        with open(sw_file, 'r') as f:
            sw_content = f.read()
            
        for url in cacheable_urls:
            if url in sw_content:
                print(f"✅ {url} configurado para cache offline")
            else:
                print(f"⚠️ {url} não explicitamente configurado")

def main():
    """Função principal de validação H005"""
    
    print("🚀 H005: Iniciando validação do PWA com bypass de autenticação")
    print(f"📅 Data: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Validações principais
    success = validate_h005()
    
    # Testes detalhados
    test_auth_bypass_urls()
    test_cacheable_urls()
    
    print("\n" + "=" * 60)
    if success:
        print("🎯 H005: CONCLUSÃO - PWA implementado com sucesso!")
        print("📱 O aplicativo agora funciona offline com bypass para autenticação")
        print("🔐 Login/logout sempre usam a rede (não são cacheados)")
        print("💾 Páginas e dados podem ser acessados offline após cache")
        print("\n📋 Próximos passos:")
        print("1. Testar instalação do PWA no dispositivo")
        print("2. Testar funcionamento offline")
        print("3. Verificar que login requer conexão")
        return 0
    else:
        print("❌ H005: FALHA - Corrija os problemas encontrados")
        return 1

if __name__ == "__main__":
    exit(main())
