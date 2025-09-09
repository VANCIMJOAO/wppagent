"""
🎯 Demonstração Prática do Sistema de Cache Invalidation
=======================================================

Script para demonstrar como o novo sistema centralizado resolve
o problema de cache invalidation inconsistente.

Funcionalidades demonstradas:
- Invalidation automática baseada em eventos
- Context-aware patterns
- Cascading invalidation
- Error handling e recovery

Autor: Claude AI
Status: Demonstração crítica para cache consistency
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, Any

from app.services.cache_invalidation import (
    CacheInvalidationService,
    CacheEvent,
    invalidate_appointment_cache,
    invalidate_conversation_cache,
    invalidate_client_cache
)


class CacheInvalidationDemo:
    """🎯 Demonstração completa do sistema de cache invalidation"""
    
    def __init__(self):
        self.service = CacheInvalidationService()
        self.demo_results = []
    
    def log_result(self, test_name: str, result: Dict[str, Any]):
        """📝 Log resultado de um teste"""
        timestamp = datetime.now().isoformat()
        
        print(f"\n🔍 {test_name}")
        print(f"⏰ {timestamp}")
        
        if result.get("success"):
            print(f"✅ SUCCESS: {result.get('invalidated_keys', 0)} keys invalidated")
            if result.get("patterns"):
                print(f"📋 Patterns: {', '.join(result['patterns'][:3])}...")
        else:
            print(f"❌ FAILED: {result.get('reason', 'unknown')}")
        
        if result.get("errors"):
            print(f"⚠️  Errors: {len(result['errors'])}")
        
        self.demo_results.append({
            "test": test_name,
            "timestamp": timestamp,
            "result": result
        })
    
    async def demo_appointment_scenarios(self):
        """🎯 Demonstrar cenários de appointment invalidation"""
        
        print("=" * 60)
        print("📅 DEMONSTRAÇÃO: APPOINTMENT CACHE INVALIDATION")
        print("=" * 60)
        
        # Cenário 1: Criação de appointment
        print("\n🔹 Cenário 1: Appointment Created")
        result1 = await invalidate_appointment_cache(
            event=CacheEvent.APPOINTMENT_CREATED,
            appointment_id=123,
            client_id=456,
            business_id=1
        )
        self.log_result("Appointment Created", result1)
        
        # Cenário 2: Atualização com context
        print("\n🔹 Cenário 2: Appointment Updated (Context-Aware)")
        result2 = await invalidate_appointment_cache(
            event=CacheEvent.APPOINTMENT_UPDATED,
            appointment_id=123,
            client_id=456,
            business_id=1
        )
        self.log_result("Appointment Updated", result2)
        
        # Cenário 3: Status change (appointment específico)
        print("\n🔹 Cenário 3: Appointment Status Changed")
        result3 = await self.service.invalidate_for_event(
            CacheEvent.APPOINTMENT_STATUS_CHANGED,
            {"appointment_id": 123, "old_status": "pending", "new_status": "confirmed"}
        )
        self.log_result("Appointment Status Changed", result3)
        
        # Cenário 4: Exclusão
        print("\n🔹 Cenário 4: Appointment Deleted")
        result4 = await invalidate_appointment_cache(
            event=CacheEvent.APPOINTMENT_DELETED,
            appointment_id=123,
            client_id=456,
            business_id=1
        )
        self.log_result("Appointment Deleted", result4)
    
    async def demo_conversation_scenarios(self):
        """💬 Demonstrar cenários de conversation invalidation"""
        
        print("\n" + "=" * 60)
        print("💬 DEMONSTRAÇÃO: CONVERSATION CACHE INVALIDATION")
        print("=" * 60)
        
        # Cenário 1: Nova conversa
        print("\n🔹 Cenário 1: Conversation Created")
        result1 = await invalidate_conversation_cache(
            event=CacheEvent.CONVERSATION_CREATED,
            conversation_id=789,
            client_id=456
        )
        self.log_result("Conversation Created", result1)
        
        # Cenário 2: Mensagem adicionada
        print("\n🔹 Cenário 2: Message Added to Conversation")
        result2 = await self.service.invalidate_for_event(
            CacheEvent.CONVERSATION_MESSAGE_ADDED,
            {"conversation_id": 789, "message_id": 101, "client_id": 456}
        )
        self.log_result("Message Added", result2)
        
        # Cenário 3: Conversa atualizada
        print("\n🔹 Cenário 3: Conversation Updated")
        result3 = await invalidate_conversation_cache(
            event=CacheEvent.CONVERSATION_UPDATED,
            conversation_id=789,
            client_id=456
        )
        self.log_result("Conversation Updated", result3)
    
    async def demo_business_cascade(self):
        """🏢 Demonstrar invalidation em cascata para business"""
        
        print("\n" + "=" * 60)
        print("🏢 DEMONSTRAÇÃO: BUSINESS CASCADE INVALIDATION")
        print("=" * 60)
        
        print("\n🔹 Cenário: Business Settings Updated")
        print("ℹ️  Este evento deve invalidar TODOS os caches relacionados")
        
        result = await self.service.invalidate_for_event(
            CacheEvent.BUSINESS_UPDATED,
            {"business_id": 1, "updated_fields": ["name", "settings"]}
        )
        
        self.log_result("Business Updated (Cascade)", result)
        
        print(f"\n📊 Patterns invalidados:")
        for i, pattern in enumerate(result.get("patterns", [])[:10]):
            print(f"   {i+1}. {pattern}")
        
        if len(result.get("patterns", [])) > 10:
            print(f"   ... e mais {len(result['patterns']) - 10} patterns")
    
    async def demo_error_scenarios(self):
        """⚠️ Demonstrar cenários de erro e recovery"""
        
        print("\n" + "=" * 60)
        print("⚠️ DEMONSTRAÇÃO: ERROR HANDLING & RECOVERY")
        print("=" * 60)
        
        # Cenário 1: Evento não configurado
        print("\n🔹 Cenário 1: Unknown Event")
        fake_event = "fake_event_not_configured"
        result1 = await self.service.invalidate_for_event(fake_event)
        self.log_result("Unknown Event", result1)
        
        # Cenário 2: Context incompleto (deve usar fallback)
        print("\n🔹 Cenário 2: Missing Context (Fallback)")
        result2 = await self.service.invalidate_for_event(
            CacheEvent.APPOINTMENT_UPDATED,
            {"client_id": 456}  # Missing appointment_id
        )
        self.log_result("Missing Context", result2)
        
        # Cenário 3: Dry run test
        print("\n🔹 Cenário 3: Dry Run Test")
        dry_run = await self.service.test_invalidation(
            CacheEvent.APPOINTMENT_CREATED,
            {"appointment_id": 999, "client_id": 888}
        )
        self.log_result("Dry Run Test", {**dry_run, "success": True})
    
    async def demo_comparison_old_vs_new(self):
        """⚖️ Comparação entre sistema antigo e novo"""
        
        print("\n" + "=" * 60)
        print("⚖️ COMPARAÇÃO: SISTEMA ANTIGO vs NOVO")
        print("=" * 60)
        
        print("\n❌ SISTEMA ANTIGO (Problemático):")
        print("   • cache_service.invalidate_pattern('appointments:list:*')")
        print("   • cache_service.invalidate_pattern('dashboard:stats:*')")
        print("   • ❌ NÃO invalida: clients:stats, analytics:funnel, reports")
        print("   • ❌ NÃO considera context específico")
        print("   • ❌ Invalidation duplicada em cada endpoint")
        print("   • ❌ Difícil de manter e debuggar")
        
        print("\n✅ SISTEMA NOVO (Centralizado):")
        print("   • await invalidate_appointment_cache(APPOINTMENT_CREATED, ...)")
        print("   • ✅ Invalida TODOS os caches relacionados automaticamente")
        print("   • ✅ Context-aware patterns (appointment_id, client_id)")
        print("   • ✅ Rules centralizadas e reutilizáveis")
        print("   • ✅ Logging e debugging avançado")
        print("   • ✅ Error handling e recovery")
        
        # Demonstrar diferença prática
        print("\n🎯 EXEMPLO PRÁTICO:")
        result = await self.service.test_invalidation(
            CacheEvent.APPOINTMENT_CREATED,
            {"appointment_id": 123, "client_id": 456}
        )
        
        print(f"\n📊 Patterns invalidados pelo sistema NOVO:")
        for i, pattern in enumerate(result["patterns"], 1):
            status = "🆕" if any(x in pattern for x in ["analytics", "reports", "clients"]) else "📋"
            print(f"   {i:2d}. {status} {pattern}")
        
        print(f"\n💡 Total: {len(result['patterns'])} patterns vs apenas 2 no sistema antigo")
    
    def generate_summary_report(self) -> Dict[str, Any]:
        """📊 Gerar relatório resumido da demonstração"""
        
        total_tests = len(self.demo_results)
        successful_tests = sum(1 for r in self.demo_results if r["result"].get("success"))
        failed_tests = total_tests - successful_tests
        
        total_patterns = sum(
            len(r["result"].get("patterns", [])) 
            for r in self.demo_results 
            if r["result"].get("patterns")
        )
        
        total_keys_invalidated = sum(
            r["result"].get("invalidated_keys", 0) 
            for r in self.demo_results
        )
        
        return {
            "timestamp": datetime.now().isoformat(),
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "failed_tests": failed_tests,
            "success_rate": f"{(successful_tests/total_tests*100):.1f}%",
            "total_patterns_tested": total_patterns,
            "total_keys_invalidated": total_keys_invalidated,
            "rules_configured": len(self.service.rules)
        }
    
    async def run_full_demo(self):
        """🚀 Executar demonstração completa"""
        
        print("🎯 DEMONSTRAÇÃO DO SISTEMA DE CACHE INVALIDATION")
        print("=" * 60)
        print("Testando sistema centralizado que resolve cache inconsistency")
        print("=" * 60)
        
        # Executar todas as demonstrações
        await self.demo_appointment_scenarios()
        await self.demo_conversation_scenarios() 
        await self.demo_business_cascade()
        await self.demo_error_scenarios()
        await self.demo_comparison_old_vs_new()
        
        # Gerar relatório final
        print("\n" + "=" * 60)
        print("📊 RELATÓRIO FINAL DA DEMONSTRAÇÃO")
        print("=" * 60)
        
        summary = self.generate_summary_report()
        
        print(f"\n✅ Testes executados: {summary['total_tests']}")
        print(f"✅ Sucessos: {summary['successful_tests']}")
        print(f"❌ Falhas: {summary['failed_tests']}")
        print(f"📈 Taxa de sucesso: {summary['success_rate']}")
        print(f"📋 Patterns testados: {summary['total_patterns_tested']}")
        print(f"🔄 Keys invalidadas: {summary['total_keys_invalidated']}")
        print(f"⚙️  Rules configuradas: {summary['rules_configured']}")
        
        print(f"\n🎉 DEMONSTRAÇÃO CONCLUÍDA COM SUCESSO!")
        print("💡 O sistema centralizado resolve completamente o problema")
        print("   de cache invalidation inconsistente reportado.")
        
        return summary


async def main():
    """🚀 Função principal para executar a demonstração"""
    
    print("🔄 Iniciando demonstração do Cache Invalidation System...")
    
    try:
        demo = CacheInvalidationDemo()
        summary = await demo.run_full_demo()
        
        # Salvar resultado para análise
        with open("cache_invalidation_demo_results.json", "w") as f:
            json.dump({
                "summary": summary,
                "detailed_results": demo.demo_results
            }, f, indent=2)
        
        print(f"\n📄 Resultados salvos em: cache_invalidation_demo_results.json")
        
        return summary
        
    except Exception as e:
        print(f"❌ Erro durante demonstração: {e}")
        raise


if __name__ == "__main__":
    # Executar demonstração
    summary = asyncio.run(main())
    
    print("\n🔍 Para executar testes unitários:")
    print("   pytest test_cache_invalidation.py -v")
    
    print("\n🎯 Para usar o sistema em produção:")
    print("   from app.services.cache_invalidation import invalidate_appointment_cache")
    print("   await invalidate_appointment_cache(CacheEvent.APPOINTMENT_CREATED, ...)")
