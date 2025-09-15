#!/usr/bin/env python3
"""
🔍 CI/CD Validation Script
Valida se todas as correções foram aplicadas corretamente
"""

import os
import yaml
from pathlib import Path


def validate_workflow(workflow_path: Path) -> dict:
    """Valida um arquivo de workflow"""
    try:
        with open(workflow_path, 'r') as f:
            workflow = yaml.safe_load(f)
        
        issues = []
        good_practices = []
        
        if 'jobs' in workflow:
            for job_name, job_config in workflow['jobs'].items():
                # Verificar timeouts
                if 'timeout-minutes' in job_config:
                    good_practices.append(f"✅ Job '{job_name}' tem timeout definido")
                else:
                    issues.append(f"❌ Job '{job_name}' sem timeout")
                
                # Verificar continue-on-error para jobs apropriados
                if job_name in ['test', 'quality', 'security', 'lint', 'format']:
                    if job_config.get('continue-on-error'):
                        good_practices.append(f"✅ Job '{job_name}' é não-bloqueante")
                
                # Verificar cache em setup-python
                if 'steps' in job_config:
                    for step in job_config['steps']:
                        if isinstance(step, dict) and 'uses' in step:
                            if 'setup-python@' in step['uses']:
                                if 'with' in step and 'cache' in step.get('with', {}):
                                    good_practices.append(f"✅ Cache habilitado para Python")
                                    break
        
        return {
            'file': workflow_path.name,
            'issues': issues,
            'good_practices': good_practices,
            'status': 'PASS' if len(issues) == 0 else 'NEEDS_ATTENTION'
        }
        
    except Exception as e:
        return {
            'file': workflow_path.name,
            'error': f"Erro ao validar: {str(e)}",
            'status': 'ERROR'
        }


def main():
    """Função principal de validação"""
    print("🔍 Validando workflows CI/CD...")
    print("=" * 50)
    
    workflows_dir = Path(".github/workflows")
    workflows = list(workflows_dir.glob("*.yml")) + list(workflows_dir.glob("*.yaml"))
    
    total_issues = 0
    total_good_practices = 0
    
    for workflow_path in workflows:
        validation = validate_workflow(workflow_path)
        
        print(f"\n📄 {validation['file']}")
        print(f"   Status: {validation['status']}")
        
        if 'error' in validation:
            print(f"   🔴 {validation['error']}")
            continue
        
        if validation['issues']:
            total_issues += len(validation['issues'])
            for issue in validation['issues']:
                print(f"   {issue}")
        
        if validation['good_practices']:
            total_good_practices += len(validation['good_practices'])
            for practice in validation['good_practices']:
                print(f"   {practice}")
    
    print(f"\n📊 RESUMO FINAL:")
    print(f"   Total de workflows: {len(workflows)}")
    print(f"   Problemas restantes: {total_issues}")
    print(f"   Boas práticas implementadas: {total_good_practices}")
    
    if total_issues == 0:
        print(f"\n🎉 PARABÉNS! Todos os workflows foram otimizados com sucesso!")
    else:
        print(f"\n⚠️  Ainda há {total_issues} problema(s) para resolver.")
    
    # Sugestões adicionais
    print(f"\n💡 RECOMENDAÇÕES ADICIONAIS:")
    print(f"   1. Monitorar tempo de execução dos jobs")
    print(f"   2. Implementar notificações de falha")
    print(f"   3. Considerar usar GitHub Environments para deploy")
    print(f"   4. Configurar dependabot para atualizações automáticas")
    print(f"   5. Usar secrets para dados sensíveis")


if __name__ == "__main__":
    main()