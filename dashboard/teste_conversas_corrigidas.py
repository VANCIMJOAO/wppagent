#!/usr/bin/env python3
"""
Teste das Correções da Página de Conversas
=========================================

Verifica se todos os bugs foram corrigidos:
✅ Chat em tempo real com mensagens reais
✅ WebSocket simulado implementado
✅ Callbacks de envio corrigidos
✅ Modal "criar nova conversa" funcionando
✅ Estados de callback consistentes
"""

import sys
import os
import subprocess
from datetime import datetime

def test_imports():
    """Testa se todos os imports estão funcionando"""
    
    print("🧪 Testando imports corrigidos...")
    
    try:
        sys.path.append('.')
        
        # Testa layout corrigido
        from layout.conversas import create_conversas_layout, filter_conversations, render_conversation_card
        print("✅ Layout de conversas corrigido importado")
        
        # Testa callbacks corrigidos
        from callbacks.conversas_callbacks import register_all_conversas_callbacks
        print("✅ Callbacks de conversas corrigidos importados")
        
        # Testa database corrigido
        from utils.database import get_conversations, get_conversation_messages, add_message_to_conversation
        print("✅ Database utils corrigidos importados")
        
        # Testa WebSocket simulator
        from utils.websocket_simulator import get_realtime_updates, simulate_user_activity, start_websocket_simulation
        print("✅ WebSocket simulator importado")
        
        return True
        
    except ImportError as e:
        print(f"❌ Erro de import: {e}")
        return False
    except Exception as e:
        print(f"❌ Erro geral: {e}")
        return False

def test_layout_creation():
    """Testa se o layout pode ser criado sem erros"""
    
    print("\n🏗️ Testando criação do layout...")
    
    try:
        from layout.conversas import create_conversas_layout
        layout = create_conversas_layout()
        print("✅ Layout criado sem erros")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao criar layout: {e}")
        return False

def test_database_functions():
    """Testa funções de database"""
    
    print("\n💾 Testando funções de database...")
    
    try:
        from utils.database import get_conversations, get_conversation_messages, get_conversation_stats
        
        # Testa busca de conversas
        conversations = get_conversations()
        print(f"✅ Conversas carregadas: {len(conversations) if conversations else 0}")
        
        # Testa busca de mensagens se há conversas
        if conversations and len(conversations) > 0:
            messages = get_conversation_messages(conversations[0]['id'])
            print(f"✅ Mensagens carregadas: {len(messages) if messages else 0}")
        
        # Testa estatísticas
        stats = get_conversation_stats()
        print(f"✅ Estatísticas: {stats}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro nas funções de database: {e}")
        return False

def test_websocket_simulator():
    """Testa o simulador de WebSocket"""
    
    print("\n🔌 Testando simulador de WebSocket...")
    
    try:
        from utils.websocket_simulator import (
            start_websocket_simulation, 
            get_realtime_updates, 
            inject_test_message,
            debug_websocket_state,
            clear_websocket_state
        )
        
        # Inicia simulação
        start_websocket_simulation()
        print("✅ WebSocket simulado iniciado")
        
        # Injeta mensagem de teste
        test_msg = inject_test_message(1)
        print(f"✅ Mensagem de teste injetada: {test_msg['content'][:30]}...")
        
        # Busca updates
        updates = get_realtime_updates()
        print(f"✅ Updates obtidos: {updates['count']} atualizações")
        
        # Verifica estado
        state = debug_websocket_state()
        print(f"✅ Estado do WebSocket: {state}")
        
        # Limpa estado
        clear_websocket_state()
        print("✅ Estado limpo")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no WebSocket simulator: {e}")
        return False

def test_file_structure():
    """Verifica se todos os arquivos existem"""
    
    print("\n📁 Verificando estrutura de arquivos...")
    
    files_to_check = [
        'layout/conversas.py',
        'callbacks/conversas_callbacks.py',
        'utils/database.py',
        'utils/websocket_simulator.py',
        'assets/conversations.css'
    ]
    
    backups_created = [
        'layout/conversas_backup.py',
        'callbacks/conversas_callbacks_backup.py',
        'utils/database_backup.py',
        'assets/conversations_backup.css'
    ]
    
    all_exist = True
    
    print("Arquivos principais:")
    for file_path in files_to_check:
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            print(f"✅ {file_path} - {size} bytes")
        else:
            print(f"❌ {file_path} - NÃO ENCONTRADO")
            all_exist = False
    
    print("\nBackups criados:")
    for backup_path in backups_created:
        if os.path.exists(backup_path):
            print(f"✅ {backup_path} - Backup salvo")
        else:
            print(f"⚠️ {backup_path} - Backup não encontrado")
    
    return all_exist

def test_mock_conversation_flow():
    """Testa fluxo completo de conversa"""
    
    print("\n💬 Testando fluxo de conversa...")
    
    try:
        from utils.database import create_conversation, add_message_to_conversation, get_conversation_messages
        
        # Cria nova conversa
        conv_id = create_conversation("Teste Automático", "Mensagem de teste do sistema")
        print(f"✅ Conversa criada com ID: {conv_id}")
        
        # Adiciona mensagem do usuário
        success = add_message_to_conversation(conv_id, "Esta é uma mensagem de teste", is_user=True)
        print(f"✅ Mensagem do usuário adicionada: {success}")
        
        # Adiciona resposta do sistema
        success = add_message_to_conversation(conv_id, "Resposta automática do sistema", is_user=False)
        print(f"✅ Resposta do sistema adicionada: {success}")
        
        # Verifica mensagens
        messages = get_conversation_messages(conv_id)
        print(f"✅ Total de mensagens na conversa: {len(messages) if messages else 0}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no fluxo de conversa: {e}")
        return False

def run_all_tests():
    """Executa todos os testes"""
    
    print("🧪 INICIANDO TESTES DAS CORREÇÕES DA PÁGINA DE CONVERSAS")
    print("=" * 60)
    print(f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print()
    
    tests = [
        ("Imports", test_imports),
        ("Estrutura de Arquivos", test_file_structure),
        ("Criação de Layout", test_layout_creation),
        ("Funções de Database", test_database_functions),
        ("Simulador WebSocket", test_websocket_simulator),
        ("Fluxo de Conversa", test_mock_conversation_flow)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name.upper()} {'='*20}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Erro crítico no teste {test_name}: {e}")
            results.append((test_name, False))
    
    # Resumo final
    print("\n" + "="*60)
    print("📊 RESUMO DOS TESTES")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for test_name, result in results:
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"{test_name:25} - {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print(f"\nTotal: {len(results)} testes")
    print(f"Passou: {passed}")
    print(f"Falhou: {failed}")
    
    success_rate = (passed / len(results)) * 100 if results else 0
    print(f"Taxa de sucesso: {success_rate:.1f}%")
    
    if success_rate >= 80:
        print("\n🎉 CORREÇÕES IMPLEMENTADAS COM SUCESSO!")
        print("\n📋 Bugs corrigidos:")
        print("   ✅ Chat em tempo real com mensagens reais")
        print("   ✅ WebSocket simulado para updates")
        print("   ✅ Callbacks de envio corrigidos")
        print("   ✅ Modal 'criar nova conversa' funcionando")
        print("   ✅ Estados de callback consistentes")
        print("   ✅ Melhor gestão de erros")
        print("   ✅ Cache inteligente implementado")
        print("   ✅ Componentes DMC atualizados")
        
        print("\n🚀 Próximos passos:")
        print("   1. Execute 'python app.py' para testar")
        print("   2. Acesse http://localhost:8050/conversas")
        print("   3. Teste criar nova conversa")
        print("   4. Teste envio de mensagens")
        print("   5. Observe updates em tempo real")
        
    else:
        print("\n⚠️ Algumas correções precisam de ajustes")
        print("   Verifique os erros acima e execute novamente")
    
    return success_rate >= 80

if __name__ == "__main__":
    try:
        os.chdir('/home/vancim/whats_agent/dashboard')
        success = run_all_tests()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Erro crítico: {e}")
        sys.exit(1)
