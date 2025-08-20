#!/usr/bin/env python3
"""
🌟 SUPER TESTE DEFINITIVO - EXECUÇÃO COMPLETA
============================================
WhatsApp Agent System - Validação Total 2025

ESTE É O EXECUTOR COMPLETO DO SUPER TESTE EM DUAS PARTES!

🎯 EXECUÇÃO SEQUENCIAL:
═══════════════════════
1. 🚀 PARTE 1: INFRAESTRUTURA E CORE
   • Conectividade e API
   • Processamento de mensagens
   • Banco de dados core
   • Segurança e validação
   • Performance e concorrência

2. 🌟 PARTE 2: FUNCIONALIDADES AVANÇADAS
   • Sistema de agendamentos completo
   • Inteligência artificial
   • Regras de negócio avançadas
   • Analytics e métricas
   • Integrações end-to-end

🏆 RELATÓRIO CONSOLIDADO FINAL
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Dict, Any
import sys
import os

# Importar as classes de teste
try:
    from super_test_part1 import SuperTesterPart1, main as main_part1
    from super_test_part2 import SuperTesterPart2, main as main_part2
except ImportError as e:
    print(f"❌ Erro ao importar módulos de teste: {e}")
    print("📌 Certifique-se de que os arquivos super_test_part1.py e super_test_part2.py estão no mesmo diretório")
    sys.exit(1)


class SuperTestExecutor:
    def __init__(self):
        self.session_id = f"SUPER_TEST_COMPLETE_{int(time.time())}"
        self.execution_start = datetime.now()
        
        # Resultados das duas partes
        self.part1_report = None
        self.part2_report = None
        
    def print_banner(self):
        """Exibe banner inicial"""
        print("🌟" + "="*98 + "🌟")
        print("🚀" + " "*96 + "🚀")
        print("🎯" + " SUPER TESTE DEFINITIVO - VALIDAÇÃO COMPLETA DO SISTEMA WHATSAPP AGENT ".center(96) + "🎯")
        print("✨" + " "*96 + "✨")
        print("🌟" + "="*98 + "🌟")
        print()
        print("📋 ESCOPO COMPLETO:")
        print("   🚀 PARTE 1: Infraestrutura & Core (5 categorias, 7 testes)")
        print("   🌟 PARTE 2: Funcionalidades Avançadas (6 categorias, 5 testes)")
        print("   📊 Total: 12 testes abrangentes com validação completa")
        print()
        print(f"🆔 ID da Sessão: {self.session_id}")
        print(f"📅 Iniciado: {self.execution_start.strftime('%d/%m/%Y às %H:%M:%S')}")
        print("="*100)
    
    async def execute_part1(self) -> bool:
        """Executa Parte 1 - Infraestrutura e Core"""
        print("\n🚀 INICIANDO PARTE 1: INFRAESTRUTURA E CORE")
        print("="*60)
        
        try:
            tester1 = SuperTesterPart1()
            self.part1_report = await tester1.run_all_tests()
            
            success = self.part1_report.get("overall_success", False)
            
            if success:
                print("\n✅ PARTE 1 CONCLUÍDA COM SUCESSO!")
                print("🎯 Infraestrutura validada - prosseguindo para Parte 2...")
                return True
            else:
                print("\n⚠️ PARTE 1 COM RESSALVAS")
                
                # Verificar se críticos passaram
                critical_rate = self.part1_report.get("critical_success_rate", 0)
                if critical_rate >= 80:
                    print("✅ Funcionalidades críticas aprovadas - prosseguindo...")
                    return True
                else:
                    print("❌ Muitas falhas críticas - interrompendo execução")
                    return False
                    
        except Exception as e:
            print(f"💥 ERRO NA PARTE 1: {e}")
            return False
    
    async def execute_part2(self) -> bool:
        """Executa Parte 2 - Funcionalidades Avançadas"""
        print("\n🌟 INICIANDO PARTE 2: FUNCIONALIDADES AVANÇADAS")
        print("="*60)
        
        try:
            tester2 = SuperTesterPart2()
            self.part2_report = await tester2.run_advanced_tests()
            
            success = self.part2_report.get("overall_success", False)
            
            if success:
                print("\n✅ PARTE 2 CONCLUÍDA COM SUCESSO!")
                print("🎉 Funcionalidades avançadas validadas!")
                return True
            else:
                print("\n⚠️ PARTE 2 COM RESSALVAS")
                print("📊 Veja o relatório para detalhes específicos")
                return False
                
        except Exception as e:
            print(f"💥 ERRO NA PARTE 2: {e}")
            return False
    
    def generate_consolidated_report(self) -> Dict[str, Any]:
        """Gera relatório consolidado das duas partes"""
        end_time = datetime.now()
        total_time = (end_time - self.execution_start).total_seconds()
        
        # Agregar dados das duas partes
        part1_data = self.part1_report or {}
        part2_data = self.part2_report or {}
        
        # Calcular estatísticas consolidadas
        total_tests = part1_data.get("total_tests", 0) + part2_data.get("total_tests", 0)
        passed_tests = part1_data.get("passed_tests", 0) + part2_data.get("passed_tests", 0)
        total_records = part1_data.get("total_records_processed", 0) + part2_data.get("total_records_processed", 0)
        
        overall_success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        # Determinar status geral
        part1_success = part1_data.get("overall_success", False)
        part2_success = part2_data.get("overall_success", False)
        
        if part1_success and part2_success:
            overall_status = "SYSTEM_PERFECT"
            status_message = "🌟 SISTEMA PERFEITO!"
        elif part1_success:
            overall_status = "SYSTEM_FUNCTIONAL"
            status_message = "✅ SISTEMA FUNCIONAL"
        else:
            overall_status = "SYSTEM_NEEDS_WORK"
            status_message = "⚠️ SISTEMA PRECISA DE CORREÇÕES"
        
        consolidated_report = {
            "session_id": self.session_id,
            "execution_start": self.execution_start.isoformat(),
            "execution_end": end_time.isoformat(),
            "total_execution_time": round(total_time, 2),
            "overall_status": overall_status,
            "status_message": status_message,
            "overall_success_rate": round(overall_success_rate, 1),
            "total_tests_executed": total_tests,
            "total_tests_passed": passed_tests,
            "total_records_processed": total_records,
            "part1_report": part1_data,
            "part2_report": part2_data,
            "infrastructure_validated": part1_success,
            "features_validated": part2_success,
            "production_ready": part1_success and part2_success
        }
        
        return consolidated_report
    
    def print_final_summary(self, consolidated_report: Dict[str, Any]):
        """Imprime relatório final consolidado"""
        print("\n" + "🌟"*50)
        print("🏆 RELATÓRIO FINAL CONSOLIDADO - SUPER TESTE")
        print("🌟"*50)
        
        print(f"\n📊 ESTATÍSTICAS GERAIS:")
        print(f"   🆔 Sessão: {consolidated_report['session_id']}")
        print(f"   ⏱️ Tempo total: {consolidated_report['total_execution_time']:.2f}s")
        print(f"   📈 Taxa de sucesso geral: {consolidated_report['overall_success_rate']:.1f}%")
        print(f"   📝 Total de testes: {consolidated_report['total_tests_executed']}")
        print(f"   ✅ Testes aprovados: {consolidated_report['total_tests_passed']}")
        print(f"   📊 Registros processados: {consolidated_report['total_records_processed']}")
        
        print(f"\n📋 RESULTADOS POR PARTE:")
        
        # Parte 1
        part1 = consolidated_report.get('part1_report', {})
        if part1:
            part1_status = "✅" if part1.get('overall_success') else "⚠️" 
            print(f"   {part1_status} PARTE 1 (Infraestrutura): {part1.get('success_rate', 0):.1f}% - {part1.get('conclusion', 'N/A')}")
            
            categories_p1 = part1.get('category_summary', {})
            for category, data in categories_p1.items():
                icon_map = {"CONNECTIVITY": "🔗", "MESSAGING": "📨", "DATABASE_CORE": "🗄️", "SECURITY": "🛡️", "PERFORMANCE": "⚡"}
                icon = icon_map.get(category, "📝")
                print(f"      {icon} {category}: {data.get('success_rate', 0):.1f}%")
        
        # Parte 2
        part2 = consolidated_report.get('part2_report', {})
        if part2:
            part2_status = "✅" if part2.get('overall_success') else "⚠️"
            ux_score = part2.get('avg_user_experience_score', 0)
            print(f"   {part2_status} PARTE 2 (Funcionalidades): {part2.get('success_rate', 0):.1f}% - UX: {ux_score:.1f}% - {part2.get('conclusion', 'N/A')}")
            
            categories_p2 = part2.get('category_summary', {})
            for category, data in categories_p2.items():
                icon_map = {"APPOINTMENTS": "📅", "AI_PROCESSING": "🤖", "BUSINESS_RULES": "💼", "ANALYTICS": "📊"}
                icon = icon_map.get(category, "📝")
                avg_ux = data.get('avg_ux_score', 0)
                print(f"      {icon} {category}: {data.get('success_rate', 0):.1f}% (UX: {avg_ux:.1f}%)")
        
        print(f"\n🏆 CONCLUSÃO FINAL:")
        print(f"   {consolidated_report['status_message']}")
        
        if consolidated_report['production_ready']:
            print("   🚀 SISTEMA 100% VALIDADO PARA PRODUÇÃO")
            print("   ✅ Infraestrutura sólida")
            print("   ✅ Funcionalidades completas")
            print("   ✅ Experiência do usuário aprovada")
            print("   🎯 Pronto para uso em escala")
        elif consolidated_report['infrastructure_validated']:
            print("   🔧 SISTEMA PARCIALMENTE VALIDADO")
            print("   ✅ Infraestrutura aprovada")
            print("   ⚠️ Funcionalidades precisam de ajustes")
            print("   📋 Revisar relatório da Parte 2")
        else:
            print("   🚨 SISTEMA PRECISA DE CORREÇÕES")
            print("   ❌ Infraestrutura com problemas")
            print("   📋 Revisar relatório da Parte 1")
            print("   🔧 Correções obrigatórias antes de prosseguir")
        
        # Recomendações
        print(f"\n🎯 PRÓXIMOS PASSOS:")
        if consolidated_report['production_ready']:
            print("   1. 🚀 Deploy em produção")
            print("   2. 📊 Monitoramento contínuo")
            print("   3. 🔄 Testes periódicos de regressão")
        elif consolidated_report['infrastructure_validated']:
            print("   1. 🔧 Corrigir issues da Parte 2")
            print("   2. 🔄 Re-executar Parte 2")
            print("   3. 📊 Validar melhorias")
        else:
            print("   1. 🔧 Corrigir issues críticas da Parte 1")
            print("   2. 🔄 Re-executar testes completos")
            print("   3. 📋 Revisão de arquitetura se necessário")
        
        print("🌟"*50)
        
        # Salvar relatório
        filename = f"SUPER_TEST_CONSOLIDATED_REPORT_{self.session_id}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(consolidated_report, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\n📄 Relatório consolidado salvo: {filename}")
        
        return consolidated_report
    
    async def run_complete_test(self) -> bool:
        """Executa o super teste completo"""
        self.print_banner()
        
        try:
            # Executar Parte 1
            part1_success = await self.execute_part1()
            
            if not part1_success:
                print("\n🛑 EXECUÇÃO INTERROMPIDA - Falhas críticas na Parte 1")
                # Ainda assim gera relatório do que foi executado
                consolidated_report = self.generate_consolidated_report()
                self.print_final_summary(consolidated_report)
                return False
            
            print("\n" + "="*60)
            print("🔄 TRANSIÇÃO: Parte 1 ➜ Parte 2")
            print("="*60)
            print("⏳ Aguardando 3 segundos para estabilização...")
            await asyncio.sleep(3)
            
            # Executar Parte 2
            part2_success = await self.execute_part2()
            
            print("\n" + "="*60)
            print("📊 CONSOLIDANDO RESULTADOS...")
            print("="*60)
            
            # Gerar relatório consolidado
            consolidated_report = self.generate_consolidated_report()
            self.print_final_summary(consolidated_report)
            
            return part1_success and part2_success
            
        except KeyboardInterrupt:
            print("\n\n⏹️ EXECUÇÃO INTERROMPIDA PELO USUÁRIO")
            return False
        except Exception as e:
            print(f"\n💥 ERRO DURANTE EXECUÇÃO COMPLETA: {e}")
            return False


async def main():
    """Função principal"""
    print("🌟 SUPER TESTE DEFINITIVO - SISTEMA WHATSAPP AGENT")
    print("🎯 Validação completa em duas partes")
    print("="*60)
    
    executor = SuperTestExecutor()
    
    try:
        success = await executor.run_complete_test()
        
        if success:
            print("\n🎉 SUPER TESTE CONCLUÍDO COM SUCESSO TOTAL!")
            print("🌟 SISTEMA WHATSAPP AGENT 100% VALIDADO!")
            return True
        else:
            print("\n⚠️ Super teste concluído com ressalvas")
            print("📊 Consulte os relatórios para detalhes")
            return False
            
    except Exception as e:
        print(f"\n💥 Erro durante super teste: {e}")
        return False


if __name__ == "__main__":
    print("🌟 EXECUTANDO SUPER TESTE DEFINITIVO COMPLETO")
    result = asyncio.run(main())
    
    if result:
        print("\n✅ Execução finalizada com sucesso!")
        sys.exit(0)
    else:
        print("\n⚠️ Execução finalizada com ressalvas - verifique os logs")
        sys.exit(1)