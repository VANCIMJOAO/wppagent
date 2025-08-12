#!/usr/bin/env python3
"""
🧪 SISTEMA DE VALIDAÇÃO COMPLETA - WHATSAPP AGENT
================================================

Testa todas as funcionalidades após correção de segurança
- Validação de conexões API
- Teste de autenticação 
- Verificação de banco de dados
- Monitoramento de segurança
"""

import os
import sys
import json
import asyncio
import logging
import requests
import psycopg2
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('SecurityValidator')

class SecurityValidator:
    """Validador completo de segurança pós-remediação"""
    
    def __init__(self):
        self.base_path = "/home/vancim/whats_agent"
        load_dotenv()
        
        self.test_results = {
            'timestamp': datetime.now().isoformat(),
            'tests': {},
            'overall_status': 'PENDING'
        }
        
        logger.info("🧪 Iniciando validação completa de segurança")
    
    def test_database_connection(self) -> bool:
        """Testa conexão com PostgreSQL usando novas credenciais"""
        logger.info("🔧 Testando conexão com banco de dados...")
        
        try:
            conn_params = {
                'host': os.getenv('DB_HOST', 'localhost'),
                'port': os.getenv('DB_PORT', '5432'),
                'database': os.getenv('DB_NAME', 'whats_agent'),
                'user': os.getenv('DB_USER', 'vancimj'),
                'password': os.getenv('DB_PASSWORD')
            }
            
            if not conn_params['password']:
                raise Exception("Senha do banco não encontrada no .env")
            
            # Tentar conexão
            conn = psycopg2.connect(**conn_params)
            cursor = conn.cursor()
            
            # Executar query de teste
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            
            # Testar tabela de usuários se existir
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'users'
                );
            """)
            users_table_exists = cursor.fetchone()[0]
            
            cursor.close()
            conn.close()
            
            self.test_results['tests']['database'] = {
                'status': 'PASSED',
                'version': version,
                'users_table': users_table_exists,
                'connection_time': time.time()
            }
            
            logger.info("  ✅ Banco de dados: CONECTADO")
            logger.info(f"  📊 PostgreSQL: {version[:50]}...")
            logger.info(f"  🗃️ Tabela users: {'Existe' if users_table_exists else 'Não encontrada'}")
            
            return True
            
        except Exception as e:
            self.test_results['tests']['database'] = {
                'status': 'FAILED',
                'error': str(e),
                'connection_time': time.time()
            }
            
            logger.error(f"  ❌ Banco de dados: ERRO - {e}")
            return False
    
    def test_openai_api(self) -> bool:
        """Testa conexão com OpenAI API"""
        logger.info("🤖 Testando OpenAI API...")
        
        try:
            api_key = os.getenv('OPENAI_API_KEY')
            
            if not api_key or api_key.startswith('REPLACE_WITH_NEW_') or api_key.startswith('sk-1c561'):
                raise Exception("OpenAI API Key não configurada ou placeholder não substituído")
            
            # Testar com endpoint de modelos (mais leve)
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(
                'https://api.openai.com/v1/models',
                headers=headers,
                timeout=15
            )
            
            if response.status_code == 200:
                models_data = response.json()
                model_count = len(models_data.get('data', []))
                
                self.test_results['tests']['openai'] = {
                    'status': 'PASSED',
                    'model_count': model_count,
                    'api_key_prefix': api_key[:20] + "...",
                    'response_time': response.elapsed.total_seconds()
                }
                
                logger.info("  ✅ OpenAI API: CONECTADO")
                logger.info(f"  📊 Modelos disponíveis: {model_count}")
                logger.info(f"  🔑 Chave API: {api_key[:15]}...")
                
                return True
            else:
                raise Exception(f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.test_results['tests']['openai'] = {
                'status': 'FAILED',
                'error': str(e)
            }
            
            logger.error(f"  ❌ OpenAI API: ERRO - {e}")
            return False
    
    def test_meta_whatsapp_api(self) -> bool:
        """Testa conexão com Meta/WhatsApp API"""
        logger.info("📱 Testando Meta/WhatsApp API...")
        
        try:
            access_token = os.getenv('META_ACCESS_TOKEN')
            
            if not access_token or access_token == 'REPLACE_WITH_NEW_META_TOKEN':
                raise Exception("Meta Access Token não configurado ou placeholder não substituído")
            
            # Testar com endpoint básico do Graph API
            response = requests.get(
                'https://graph.facebook.com/v18.0/me',
                params={'access_token': access_token},
                timeout=15
            )
            
            if response.status_code == 200:
                profile_data = response.json()
                
                # Testar endpoint específico do WhatsApp se phone_number_id estiver configurado
                phone_number_id = os.getenv('PHONE_NUMBER_ID')
                whatsapp_status = None
                
                if phone_number_id:
                    whatsapp_response = requests.get(
                        f'https://graph.facebook.com/v18.0/{phone_number_id}',
                        params={'access_token': access_token},
                        timeout=15
                    )
                    whatsapp_status = whatsapp_response.status_code == 200
                
                self.test_results['tests']['meta_whatsapp'] = {
                    'status': 'PASSED',
                    'profile_id': profile_data.get('id'),
                    'token_prefix': access_token[:20] + "...",
                    'whatsapp_accessible': whatsapp_status,
                    'phone_number_id': phone_number_id,
                    'response_time': response.elapsed.total_seconds()
                }
                
                logger.info("  ✅ Meta/WhatsApp API: CONECTADO")
                logger.info(f"  🆔 Profile ID: {profile_data.get('id')}")
                logger.info(f"  📞 WhatsApp Phone ID: {phone_number_id}")
                logger.info(f"  🔑 Token: {access_token[:15]}...")
                
                return True
            else:
                raise Exception(f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.test_results['tests']['meta_whatsapp'] = {
                'status': 'FAILED',
                'error': str(e)
            }
            
            logger.error(f"  ❌ Meta/WhatsApp API: ERRO - {e}")
            return False
    
    def test_ngrok_connection(self) -> bool:
        """Testa conexão com Ngrok"""
        logger.info("🌐 Testando Ngrok...")
        
        try:
            auth_token = os.getenv('NGROK_AUTHTOKEN')
            
            if not auth_token or auth_token == 'REPLACE_WITH_NEW_NGROK_TOKEN':
                raise Exception("Ngrok Auth Token não configurado ou placeholder não substituído")
            
            # Testar com API do Ngrok
            headers = {
                'Authorization': f'Bearer {auth_token}',
                'Ngrok-Version': '2'
            }
            
            response = requests.get(
                'https://api.ngrok.com/tunnels',
                headers=headers,
                timeout=15
            )
            
            if response.status_code == 200:
                tunnels_data = response.json()
                tunnel_count = len(tunnels_data.get('tunnels', []))
                
                self.test_results['tests']['ngrok'] = {
                    'status': 'PASSED',
                    'tunnel_count': tunnel_count,
                    'token_prefix': auth_token[:20] + "...",
                    'response_time': response.elapsed.total_seconds()
                }
                
                logger.info("  ✅ Ngrok: CONECTADO")
                logger.info(f"  🔗 Túneis ativos: {tunnel_count}")
                logger.info(f"  🔑 Token: {auth_token[:15]}...")
                
                return True
            else:
                raise Exception(f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.test_results['tests']['ngrok'] = {
                'status': 'FAILED',
                'error': str(e)
            }
            
            logger.error(f"  ❌ Ngrok: ERRO - {e}")
            return False
    
    def test_admin_credentials(self) -> bool:
        """Testa novas credenciais de admin"""
        logger.info("👤 Testando credenciais de admin...")
        
        try:
            admin_username = os.getenv('ADMIN_USERNAME', 'admin')
            admin_password = os.getenv('ADMIN_PASSWORD')
            
            if not admin_password:
                raise Exception("Senha de admin não encontrada no .env")
            
            if admin_password == '[SENHA_ANTERIOR_REMOVIDA]':
                raise Exception("Senha de admin ainda é a padrão insegura!")
            
            # Verificar força da senha
            password_strength = {
                'length': len(admin_password),
                'has_uppercase': any(c.isupper() for c in admin_password),
                'has_lowercase': any(c.islower() for c in admin_password),
                'has_digits': any(c.isdigit() for c in admin_password),
                'has_special': any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in admin_password)
            }
            
            strength_score = sum(password_strength.values()) - 1  # Descontar length
            is_strong = password_strength['length'] >= 12 and strength_score >= 3
            
            self.test_results['tests']['admin_credentials'] = {
                'status': 'PASSED' if is_strong else 'WARNING',
                'username': admin_username,
                'password_strength': password_strength,
                'is_strong': is_strong,
                'password_preview': admin_password[:4] + '*' * (len(admin_password) - 4)
            }
            
            logger.info("  ✅ Credenciais admin: CONFIGURADAS")
            logger.info(f"  👤 Username: {admin_username}")
            logger.info(f"  🔒 Password: {admin_password[:4]}{'*' * (len(admin_password) - 4)}")
            logger.info(f"  💪 Força: {'FORTE' if is_strong else 'MÉDIA'} ({password_strength['length']} chars)")
            
            return True
            
        except Exception as e:
            self.test_results['tests']['admin_credentials'] = {
                'status': 'FAILED',
                'error': str(e)
            }
            
            logger.error(f"  ❌ Credenciais admin: ERRO - {e}")
            return False
    
    def test_security_monitoring(self) -> bool:
        """Testa sistema de monitoramento de segurança"""
        logger.info("👁️ Testando monitoramento de segurança...")
        
        try:
            # Executar monitor de segurança
            import subprocess
            
            result = subprocess.run(
                ['python3', 'scripts/security_monitor.py'],
                cwd=self.base_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                output = result.stdout.strip()
                
                # Verificar se não há credenciais comprometidas
                is_clean = "Nenhuma credencial comprometida detectada" in output
                
                self.test_results['tests']['security_monitoring'] = {
                    'status': 'PASSED' if is_clean else 'WARNING',
                    'output': output,
                    'is_clean': is_clean,
                    'execution_time': time.time()
                }
                
                logger.info("  ✅ Monitor de segurança: EXECUTADO")
                logger.info(f"  🛡️ Status: {'LIMPO' if is_clean else 'CREDENCIAIS ENCONTRADAS'}")
                logger.info(f"  📊 Output: {output}")
                
                return True
            else:
                raise Exception(f"Exit code {result.returncode}: {result.stderr}")
                
        except Exception as e:
            self.test_results['tests']['security_monitoring'] = {
                'status': 'FAILED',
                'error': str(e)
            }
            
            logger.error(f"  ❌ Monitor de segurança: ERRO - {e}")
            return False
    
    def test_vault_access(self) -> bool:
        """Testa acesso ao vault de credenciais"""
        logger.info("🔐 Testando vault de credenciais...")
        
        try:
            vault_path = f"{self.base_path}/secrets/vault"
            
            if not os.path.exists(vault_path):
                raise Exception("Diretório do vault não encontrado")
            
            # Verificar permissões
            vault_stat = os.stat(vault_path)
            vault_perms = oct(vault_stat.st_mode)[-3:]
            
            if vault_perms != '700':
                raise Exception(f"Permissões do vault inseguras: {vault_perms} (deveria ser 700)")
            
            # Verificar arquivos do vault
            vault_files = os.listdir(vault_path)
            vault_key_exists = '.vault_key' in vault_files
            credentials_files = [f for f in vault_files if f.endswith('.vault')]
            
            self.test_results['tests']['vault'] = {
                'status': 'PASSED',
                'path': vault_path,
                'permissions': vault_perms,
                'vault_key_exists': vault_key_exists,
                'credentials_files': len(credentials_files),
                'files': vault_files
            }
            
            logger.info("  ✅ Vault: ACESSÍVEL")
            logger.info(f"  📁 Localização: {vault_path}")
            logger.info(f"  🔒 Permissões: {vault_perms} (seguro)")
            logger.info(f"  🗝️ Chave do vault: {'Existe' if vault_key_exists else 'Não encontrada'}")
            logger.info(f"  📦 Arquivos de credenciais: {len(credentials_files)}")
            
            return True
            
        except Exception as e:
            self.test_results['tests']['vault'] = {
                'status': 'FAILED',
                'error': str(e)
            }
            
            logger.error(f"  ❌ Vault: ERRO - {e}")
            return False
    
    def check_placeholder_remaining(self) -> bool:
        """Verifica se ainda há placeholders no .env"""
        logger.info("🔍 Verificando placeholders restantes...")
        
        try:
            env_file = f"{self.base_path}/.env"
            
            with open(env_file, 'r') as f:
                content = f.read()
            
            placeholders = []
            placeholder_patterns = [
                'REPLACE_WITH_NEW_OPENAI_KEY',
                'REPLACE_WITH_NEW_META_TOKEN',
                'REPLACE_WITH_NEW_NGROK_TOKEN'
            ]
            
            for pattern in placeholder_patterns:
                if pattern in content:
                    placeholders.append(pattern)
            
            has_placeholders = len(placeholders) > 0
            
            self.test_results['tests']['placeholders'] = {
                'status': 'WARNING' if has_placeholders else 'PASSED',
                'remaining_placeholders': placeholders,
                'count': len(placeholders)
            }
            
            if has_placeholders:
                logger.warning("  ⚠️ Placeholders: ENCONTRADOS")
                for placeholder in placeholders:
                    logger.warning(f"    - {placeholder}")
            else:
                logger.info("  ✅ Placeholders: NENHUM RESTANTE")
            
            return not has_placeholders
            
        except Exception as e:
            self.test_results['tests']['placeholders'] = {
                'status': 'FAILED',
                'error': str(e)
            }
            
            logger.error(f"  ❌ Verificação de placeholders: ERRO - {e}")
            return False
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Executa todos os testes de validação"""
        logger.info("🧪 INICIANDO BATERIA COMPLETA DE TESTES")
        logger.info("=" * 60)
        
        tests = [
            ('placeholders', self.check_placeholder_remaining),
            ('database', self.test_database_connection),
            ('openai', self.test_openai_api),
            ('meta_whatsapp', self.test_meta_whatsapp_api),
            ('ngrok', self.test_ngrok_connection),
            ('admin_credentials', self.test_admin_credentials),
            ('security_monitoring', self.test_security_monitoring),
            ('vault', self.test_vault_access)
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test_name, test_function in tests:
            try:
                if test_function():
                    passed_tests += 1
            except Exception as e:
                logger.error(f"Erro inesperado no teste {test_name}: {e}")
            
            logger.info("")  # Linha em branco entre testes
        
        # Calcular status geral
        success_rate = (passed_tests / total_tests) * 100
        
        if success_rate >= 90:
            overall_status = 'PASSED'
        elif success_rate >= 70:
            overall_status = 'WARNING'
        else:
            overall_status = 'FAILED'
        
        self.test_results['overall_status'] = overall_status
        self.test_results['summary'] = {
            'passed_tests': passed_tests,
            'total_tests': total_tests,
            'success_rate': success_rate
        }
        
        return self.test_results
    
    def generate_validation_report(self) -> str:
        """Gera relatório de validação"""
        logger.info("📋 Gerando relatório de validação...")
        
        results = self.test_results
        summary = results.get('summary', {})
        
        status_emoji = {
            'PASSED': '✅',
            'WARNING': '⚠️',
            'FAILED': '❌'
        }
        
        report_content = f"""# 🧪 RELATÓRIO DE VALIDAÇÃO PÓS-REMEDIAÇÃO

**Data:** {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
**Status Geral:** {status_emoji.get(results['overall_status'], '❓')} {results['overall_status']}
**Taxa de Sucesso:** {summary.get('success_rate', 0):.1f}% ({summary.get('passed_tests', 0)}/{summary.get('total_tests', 0)} testes)

---

## 📊 RESULTADOS DOS TESTES

"""
        
        for test_name, test_data in results['tests'].items():
            status = test_data.get('status', 'UNKNOWN')
            emoji = status_emoji.get(status, '❓')
            
            report_content += f"### {emoji} {test_name.upper().replace('_', ' ')}\n"
            report_content += f"**Status:** {status}\n"
            
            if status == 'FAILED':
                report_content += f"**Erro:** {test_data.get('error', 'Não especificado')}\n"
            elif status == 'PASSED':
                # Adicionar detalhes específicos do teste
                if test_name == 'database':
                    report_content += f"**Versão:** {test_data.get('version', 'N/A')[:50]}...\n"
                elif test_name == 'openai':
                    report_content += f"**Modelos:** {test_data.get('model_count', 0)}\n"
                elif test_name == 'meta_whatsapp':
                    report_content += f"**Profile ID:** {test_data.get('profile_id', 'N/A')}\n"
                elif test_name == 'admin_credentials':
                    report_content += f"**Força da senha:** {'FORTE' if test_data.get('is_strong') else 'MÉDIA'}\n"
                elif test_name == 'vault':
                    report_content += f"**Arquivos:** {test_data.get('credentials_files', 0)} credenciais\n"
            
            report_content += "\n"
        
        report_content += f"""---

## 🎯 PRÓXIMAS AÇÕES

"""
        
        if results['overall_status'] == 'PASSED':
            report_content += """✅ **SISTEMA TOTALMENTE VALIDADO**

Todas as funcionalidades estão operacionais:
- 🔐 Credenciais seguras implementadas
- 🛡️ Monitoramento ativo
- 📡 APIs conectadas
- 🗄️ Banco de dados operacional

**Recomendações:**
1. Configurar monitoramento contínuo (cron job)
2. Implementar rotação automática de credenciais
3. Agendar auditoria de segurança mensal
"""
        elif results['overall_status'] == 'WARNING':
            report_content += """⚠️ **SISTEMA PARCIALMENTE VALIDADO**

Alguns problemas foram identificados:
- Verificar testes com status WARNING
- Completar configurações pendentes
- Substituir placeholders restantes

**Ações necessárias:**
1. Revisar testes com problemas
2. Completar configuração de tokens API
3. Re-executar validação após correções
"""
        else:
            report_content += """❌ **SISTEMA COM PROBLEMAS CRÍTICOS**

Múltiplos testes falharam:
- Verificar configurações de credenciais
- Validar conectividade de rede
- Revisar logs de erro detalhados

**Ações urgentes:**
1. Corrigir todos os testes falhados
2. Verificar configuração do .env
3. Re-executar remediação se necessário
"""
        
        report_content += f"""

---

**Relatório gerado em:** {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
**Sistema:** WhatsApp Agent Security Validation v1.0
"""
        
        # Salvar relatório
        report_path = f"{self.base_path}/logs/security"
        os.makedirs(report_path, exist_ok=True)
        
        report_file = f"{report_path}/validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        # Salvar JSON dos resultados
        json_file = f"{report_path}/validation_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(json_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"📋 Relatório salvo: {report_file}")
        logger.info(f"📊 Dados JSON: {json_file}")
        
        return report_file

def main():
    """Função principal de validação"""
    print("🧪 INICIANDO VALIDAÇÃO COMPLETA DE SEGURANÇA")
    print("=" * 60)
    
    validator = SecurityValidator()
    
    try:
        # Executar todos os testes
        results = validator.run_all_tests()
        
        # Gerar relatório
        report_file = validator.generate_validation_report()
        
        # Mostrar resumo final
        summary = results.get('summary', {})
        overall_status = results.get('overall_status', 'UNKNOWN')
        
        print("🎯 RESUMO FINAL")
        print("=" * 60)
        print(f"📊 Testes executados: {summary.get('total_tests', 0)}")
        print(f"✅ Testes aprovados: {summary.get('passed_tests', 0)}")
        print(f"📈 Taxa de sucesso: {summary.get('success_rate', 0):.1f}%")
        print(f"🎯 Status geral: {overall_status}")
        print(f"📋 Relatório: {report_file}")
        
        if overall_status == 'PASSED':
            print("\n✅ VALIDAÇÃO COMPLETA BEM-SUCEDIDA!")
            print("🛡️ Sistema seguro e pronto para produção")
        elif overall_status == 'WARNING':
            print("\n⚠️ VALIDAÇÃO COM AVISOS")
            print("🔧 Algumas configurações precisam ser completadas")
        else:
            print("\n❌ VALIDAÇÃO COM PROBLEMAS")
            print("🚨 Ações corretivas necessárias")
        
        return overall_status == 'PASSED'
        
    except Exception as e:
        logger.error(f"❌ Erro durante validação: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
