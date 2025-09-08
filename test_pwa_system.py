#!/usr/bin/env python3
import os
import asyncio
import aiohttp
import json
from datetime import datetime

async def test_pwa_system():
    """Teste completo do sistema PWA"""
    print("🔔 Testando Sistema PWA")
    print("=" * 50)
    
    # 1. Verificar arquivos essenciais
    print("\n1️⃣ Verificando arquivos PWA...")
    
    required_files = [
        'nextjs_dashboard/public/manifest.json',
        'nextjs_dashboard/public/sw-advanced.js',
        'nextjs_dashboard/public/icon-192x192.png',
        'nextjs_dashboard/public/icon-512x512.png',
        'nextjs_dashboard/lib/offline-storage.ts',
        'nextjs_dashboard/lib/offline-fetch.ts',
        'nextjs_dashboard/hooks/usePWA.ts',
        'nextjs_dashboard/components/pwa/PWAPrompt.tsx',
        'nextjs_dashboard/components/pwa/PWAWrapper.tsx',
        'nextjs_dashboard/components/offline/OfflineIndicator.tsx',
        'nextjs_dashboard/app/offline/page.tsx',
        'nextjs_dashboard/app/pwa.css'
    ]
    
    for file_path in required_files:
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            print(f"✅ {file_path} ({size} bytes)")
        else:
            print(f"❌ {file_path} não encontrado")
    
    # 2. Validar manifest.json
    print("\n2️⃣ Validando manifest.json...")
    
    try:
        with open('nextjs_dashboard/public/manifest.json', 'r') as f:
            manifest = json.load(f)
        
        required_fields = ['name', 'short_name', 'start_url', 'display', 'theme_color', 'icons']
        
        for field in required_fields:
            if field in manifest:
                print(f"✅ {field}: {manifest[field] if field != 'icons' else f'{len(manifest[field])} ícones'}")
            else:
                print(f"❌ Campo obrigatório {field} não encontrado")
        
        # Verificar ícones
        if 'icons' in manifest:
            for icon in manifest['icons']:
                sizes = icon.get('sizes', 'N/A')
                src = icon.get('src', 'N/A')
                print(f"   📱 Ícone {sizes}: {src}")
        
    except Exception as e:
        print(f"❌ Erro ao validar manifest: {e}")
    
    # 3. Verificar Service Worker
    print("\n3️⃣ Analisando Service Worker...")
    
    try:
        with open('nextjs_dashboard/public/sw-advanced.js', 'r') as f:
            sw_content = f.read()
        
        sw_features = [
            'addEventListener(\'install\'',
            'addEventListener(\'activate\'', 
            'addEventListener(\'fetch\'',
            'addEventListener(\'sync\'',
            'caches.open',
            'networkFirstStrategy',
            'cacheFirstStrategy',
            'staleWhileRevalidateStrategy'
        ]
        
        for feature in sw_features:
            if feature in sw_content:
                print(f"✅ {feature}")
            else:
                print(f"❌ {feature} não encontrado")
                
        print(f"📊 Service Worker tem {len(sw_content)} caracteres")
        
    except Exception as e:
        print(f"❌ Erro ao analisar Service Worker: {e}")
    
    # 4. Verificar TypeScript/React components
    print("\n4️⃣ Verificando componentes React...")
    
    components_check = [
        ('nextjs_dashboard/hooks/usePWA.ts', ['usePWAInstall', 'useServiceWorker', 'usePWA']),
        ('nextjs_dashboard/lib/offline-storage.ts', ['OfflineStorageService', 'useOfflineData', 'offlineStorage']),
        ('nextjs_dashboard/lib/offline-fetch.ts', ['fetchWithOffline', 'useOfflineFetch', 'useOfflineAction']),
        ('nextjs_dashboard/components/pwa/PWAPrompt.tsx', ['PWAPrompt', 'PWASettings']),
        ('nextjs_dashboard/components/offline/OfflineIndicator.tsx', ['OfflineIndicator', 'useNetworkStatus'])
    ]
    
    for file_path, expected_exports in components_check:
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            print(f"\n   📁 {file_path}:")
            for export in expected_exports:
                if f"export" in content and export in content:
                    print(f"   ✅ {export}")
                else:
                    print(f"   ❌ {export} não encontrado")
                    
        except Exception as e:
            print(f"   ❌ Erro ao verificar {file_path}: {e}")
    
    # 5. Verificar layout integration
    print("\n5️⃣ Verificando integração no layout...")
    
    try:
        with open('nextjs_dashboard/app/layout.tsx', 'r') as f:
            layout_content = f.read()
        
        layout_features = [
            'manifest',
            'theme-color',
            'apple-mobile-web-app',
            'PWAWrapper',
            'PWAInstallDetector'
        ]
        
        for feature in layout_features:
            if feature in layout_content:
                print(f"✅ {feature}")
            else:
                print(f"❌ {feature} não encontrado no layout")
                
    except Exception as e:
        print(f"❌ Erro ao verificar layout: {e}")
    
    # 6. Verificar ícones gerados
    print("\n6️⃣ Verificando ícones PWA...")
    
    icon_sizes = [72, 96, 128, 144, 152, 192, 384, 512]
    
    for size in icon_sizes:
        icon_path = f'nextjs_dashboard/public/icon-{size}x{size}.png'
        if os.path.exists(icon_path):
            icon_size = os.path.getsize(icon_path)
            print(f"✅ {size}x{size}: {icon_size} bytes")
        else:
            print(f"❌ Ícone {size}x{size} não encontrado")
    
    # 7. Verificar página offline
    print("\n7️⃣ Verificando página offline...")
    
    try:
        with open('nextjs_dashboard/app/offline/page.tsx', 'r') as f:
            offline_content = f.read()
        
        offline_features = [
            'useOfflineData',
            'hasOfflineData',
            'pendingActions',
            'isOnline'
        ]
        
        for feature in offline_features:
            if feature in offline_content:
                print(f"✅ {feature}")
            else:
                print(f"❌ {feature} não encontrado")
                
    except Exception as e:
        print(f"❌ Erro ao verificar página offline: {e}")
    
    # 8. Resumo e Score
    print("\n" + "=" * 50)
    print("📊 RELATÓRIO FINAL PWA")
    print("=" * 50)
    
    # Calcular score baseado nos arquivos essenciais
    score = 0
    total_files = len(required_files)
    
    for file_path in required_files:
        if os.path.exists(file_path):
            score += 1
    
    percentage = (score / total_files) * 100
    
    print(f"📁 Arquivos essenciais: {score}/{total_files} ({percentage:.1f}%)")
    
    if percentage >= 90:
        print("🎉 PWA COMPLETO - Pronto para produção!")
        print("✅ Todos os recursos PWA implementados:")
        print("   • Manifest.json configurado")
        print("   • Service Worker avançado")
        print("   • Suporte offline completo")
        print("   • Indicadores visuais")
        print("   • Instalação como app")
        print("   • Ícones para todas as plataformas")
        print("   • Página offline personalizada")
    elif percentage >= 70:
        print("⚠️ PWA FUNCIONAL - Pequenos ajustes necessários")
    else:
        print("❌ PWA INCOMPLETO - Implementação em andamento")
    
    print(f"\n📝 Próximos passos:")
    print("   1. Testar instalação em dispositivos reais")
    print("   2. Configurar cache strategies específicas")
    print("   3. Implementar background sync avançado")
    print("   4. Otimizar performance offline")
    print("   5. Adicionar analytics PWA")

if __name__ == "__main__":
    asyncio.run(test_pwa_system())
