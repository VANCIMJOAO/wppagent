"""
🔄 Script de Migração Automática - C002  
=======================================

Script para migrar endpoints existentes para o novo padrão ApiResponse<T>.
Analisa o código atual e sugere/aplica as mudanças necessárias.

Funcionalidades:
- Analisa endpoints existentes
- Identifica padrões de response inconsistentes
- Sugere mudanças para padronização
- Gera relatório de migração
- Aplica mudanças automaticamente (opcional)

Autor: Claude AI
Data: 2025-09-11  
Status: Implementação C002 - Ferramenta de Migração
"""

import os
import re
import ast
import json
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

@dataclass
class EndpointInfo:
    """Informações sobre um endpoint"""
    file_path: str
    function_name: str
    line_number: int
    method: str
    path: str
    response_model: Optional[str]
    return_statements: List[str]
    has_error_handling: bool
    is_consistent: bool
    issues: List[str]


@dataclass
class MigrationSuggestion:
    """Sugestão de migração para um endpoint"""
    endpoint: EndpointInfo
    action: str  # "wrap_response", "add_decorator", "fix_error_handling"
    description: str
    before_code: str
    after_code: str
    priority: int  # 1=alta, 2=média, 3=baixa


class EndpointAnalyzer:
    """Analisador de endpoints para identificar inconsistências"""
    
    def __init__(self, base_path: str = "/home/vancim/whats_agent/app"):
        self.base_path = Path(base_path)
        self.endpoints = []
        self.suggestions = []
    
    def analyze_project(self) -> Dict[str, Any]:
        """Analisa todo o projeto em busca de endpoints"""
        print("🔍 Analisando endpoints do projeto...")
        
        # Buscar arquivos Python em routes/
        routes_path = self.base_path / "routes"
        if routes_path.exists():
            for py_file in routes_path.glob("*.py"):
                if py_file.name != "__init__.py":
                    self._analyze_file(py_file)
        
        # Buscar em outros diretórios relevantes
        for subdir in ["main.py", "api", "endpoints"]:
            subdir_path = self.base_path / subdir
            if subdir_path.exists():
                if subdir_path.is_file():
                    self._analyze_file(subdir_path)
                else:
                    for py_file in subdir_path.glob("**/*.py"):
                        if py_file.name != "__init__.py":
                            self._analyze_file(py_file)
        
        # Gerar sugestões
        self._generate_suggestions()
        
        return self._generate_report()
    
    def _analyze_file(self, file_path: Path):
        """Analisa um arquivo Python em busca de endpoints"""
        print(f"  📁 Analisando {file_path.relative_to(self.base_path)}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse AST
            tree = ast.parse(content)
            
            # Buscar decoradores de rota (@router.get, @router.post, etc.)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    endpoint = self._analyze_function(node, content, str(file_path))
                    if endpoint:
                        self.endpoints.append(endpoint)
                        
        except Exception as e:
            print(f"  ❌ Erro ao analisar {file_path}: {e}")
    
    def _analyze_function(self, node: ast.FunctionDef, content: str, file_path: str) -> Optional[EndpointInfo]:
        """Analisa uma função para verificar se é um endpoint"""
        
        # Verificar se tem decoradores de rota
        route_decorators = []
        response_model = None
        
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute):
                if decorator.func.attr in ['get', 'post', 'put', 'delete', 'patch']:
                    method = decorator.func.attr.upper()
                    
                    # Extrair path
                    path = "unknown"
                    if decorator.args and isinstance(decorator.args[0], ast.Constant):
                        path = decorator.args[0].value
                    
                    # Extrair response_model
                    for keyword in decorator.keywords:
                        if keyword.arg == "response_model":
                            if isinstance(keyword.value, ast.Name):
                                response_model = keyword.value.id
                            elif isinstance(keyword.value, ast.Attribute):
                                response_model = ast.unparse(keyword.value)
                    
                    route_decorators.append((method, path))
        
        if not route_decorators:
            return None
        
        # Analisar corpo da função
        lines = content.split('\n')
        function_start = node.lineno
        
        # Extrair return statements
        return_statements = []
        has_error_handling = False
        
        for stmt in ast.walk(node):
            if isinstance(stmt, ast.Return) and stmt.value:
                return_line = stmt.lineno - 1
                if return_line < len(lines):
                    return_statements.append(lines[return_line].strip())
            
            if isinstance(stmt, (ast.Try, ast.ExceptHandler)):
                has_error_handling = True
        
        # Verificar consistência
        issues = []
        is_consistent = True
        
        # Verificar se usa ApiResponse
        function_content = ast.unparse(node)
        if "ApiResponse" not in function_content:
            issues.append("Não usa ApiResponse wrapper")
            is_consistent = False
        
        # Verificar error handling
        if not has_error_handling:
            issues.append("Sem tratamento de erro adequado")
            is_consistent = False
        
        # Verificar padrão de retorno
        for return_stmt in return_statements:
            if "JSONResponse" in return_stmt and "success" not in return_stmt:
                issues.append("JSONResponse sem estrutura {success, data, error}")
                is_consistent = False
        
        method, path = route_decorators[0]  # Pegar primeiro decorador
        
        return EndpointInfo(
            file_path=file_path,
            function_name=node.name,
            line_number=function_start,
            method=method,
            path=path,
            response_model=response_model,
            return_statements=return_statements,
            has_error_handling=has_error_handling,
            is_consistent=is_consistent,
            issues=issues
        )
    
    def _generate_suggestions(self):
        """Gera sugestões de migração baseadas na análise"""
        print("🔧 Gerando sugestões de migração...")
        
        for endpoint in self.endpoints:
            if endpoint.is_consistent:
                continue
            
            # Sugestão 1: Adicionar decorador ApiResponse
            if "Não usa ApiResponse wrapper" in endpoint.issues:
                suggestion = MigrationSuggestion(
                    endpoint=endpoint,
                    action="add_decorator",
                    description=f"Adicionar decorador @api_response_wrapper() ao endpoint {endpoint.function_name}",
                    before_code=f"@router.{endpoint.method.lower()}(\"{endpoint.path}\")",
                    after_code=f"@router.{endpoint.method.lower()}(\"{endpoint.path}\")\n@api_response_wrapper()",
                    priority=1
                )
                self.suggestions.append(suggestion)
            
            # Sugestão 2: Melhorar error handling
            if "Sem tratamento de erro adequado" in endpoint.issues:
                suggestion = MigrationSuggestion(
                    endpoint=endpoint,
                    action="fix_error_handling",
                    description=f"Adicionar try/catch adequado ao endpoint {endpoint.function_name}",
                    before_code="# Sem tratamento de erro",
                    after_code="""try:
    # lógica do endpoint
    return result
except HTTPException:
    raise
except Exception as e:
    logger.error(f"Erro em {endpoint.function_name}: {e}")
    raise HTTPException(status_code=500, detail="Erro interno")""",
                    priority=2
                )
                self.suggestions.append(suggestion)
            
            # Sugestão 3: Padronizar JSONResponse
            if any("JSONResponse sem estrutura" in issue for issue in endpoint.issues):
                suggestion = MigrationSuggestion(
                    endpoint=endpoint,
                    action="wrap_response",
                    description=f"Padronizar retorno do endpoint {endpoint.function_name}",
                    before_code="return JSONResponse(content=data, status_code=200)",
                    after_code="return ApiResponse.success_response(data=data)",
                    priority=1
                )
                self.suggestions.append(suggestion)
    
    def _generate_report(self) -> Dict[str, Any]:
        """Gera relatório completo da análise"""
        
        total_endpoints = len(self.endpoints)
        consistent_endpoints = len([e for e in self.endpoints if e.is_consistent])
        inconsistent_endpoints = total_endpoints - consistent_endpoints
        
        # Agrupar por tipo de issue
        issue_counts = {}
        for endpoint in self.endpoints:
            for issue in endpoint.issues:
                issue_counts[issue] = issue_counts.get(issue, 0) + 1
        
        # Agrupar sugestões por prioridade
        high_priority = [s for s in self.suggestions if s.priority == 1]
        medium_priority = [s for s in self.suggestions if s.priority == 2]
        low_priority = [s for s in self.suggestions if s.priority == 3]
        
        report = {
            "summary": {
                "total_endpoints": total_endpoints,
                "consistent_endpoints": consistent_endpoints,
                "inconsistent_endpoints": inconsistent_endpoints,
                "consistency_percentage": (consistent_endpoints / total_endpoints * 100) if total_endpoints > 0 else 0
            },
            "issues": {
                "by_type": issue_counts,
                "most_common": sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            },
            "suggestions": {
                "total": len(self.suggestions),
                "high_priority": len(high_priority),
                "medium_priority": len(medium_priority),
                "low_priority": len(low_priority)
            },
            "endpoints": [
                {
                    "file": os.path.basename(e.file_path),
                    "function": e.function_name,
                    "method": e.method,
                    "path": e.path,
                    "consistent": e.is_consistent,
                    "issues": e.issues
                }
                for e in self.endpoints
            ],
            "migration_plan": [
                {
                    "endpoint": f"{s.endpoint.method} {s.endpoint.path}",
                    "function": s.endpoint.function_name,
                    "file": os.path.basename(s.endpoint.file_path),
                    "action": s.action,
                    "description": s.description,
                    "priority": s.priority
                }
                for s in sorted(self.suggestions, key=lambda x: x.priority)
            ]
        }
        
        return report


def main():
    """Execução principal do script de migração"""
    print("🚀 Iniciando análise de migração C002 - Padronizar Response Schemas")
    print("=" * 70)
    
    analyzer = EndpointAnalyzer()
    report = analyzer.analyze_project()
    
    # Exibir relatório
    print("\n📊 RELATÓRIO DE ANÁLISE")
    print("=" * 30)
    print(f"Total de endpoints: {report['summary']['total_endpoints']}")
    print(f"Endpoints consistentes: {report['summary']['consistent_endpoints']}")
    print(f"Endpoints inconsistentes: {report['summary']['inconsistent_endpoints']}")
    print(f"Percentual de consistência: {report['summary']['consistency_percentage']:.1f}%")
    
    print("\n🔍 ISSUES MAIS COMUNS")
    print("-" * 20)
    for issue, count in report['issues']['most_common']:
        print(f"  • {issue}: {count} ocorrências")
    
    print("\n🔧 SUGESTÕES DE MIGRAÇÃO")
    print("-" * 25)
    print(f"Alta prioridade: {report['suggestions']['high_priority']}")
    print(f"Média prioridade: {report['suggestions']['medium_priority']}")  
    print(f"Baixa prioridade: {report['suggestions']['low_priority']}")
    
    print("\n📋 PLANO DE MIGRAÇÃO")
    print("-" * 20)
    for i, suggestion in enumerate(report['migration_plan'][:10], 1):  # Top 10
        priority_icon = "🔴" if suggestion['priority'] == 1 else "🟡" if suggestion['priority'] == 2 else "🟢"
        print(f"{i:2}. {priority_icon} {suggestion['description']}")
        print(f"     📁 {suggestion['file']} → {suggestion['function']}")
    
    if len(report['migration_plan']) > 10:
        print(f"     ... e mais {len(report['migration_plan']) - 10} sugestões")
    
    # Salvar relatório
    report_path = "/home/vancim/whats_agent/temp_reports/c002_migration_analysis.json"
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Relatório completo salvo em: {report_path}")
    
    # Sugestões de próximos passos
    print("\n🎯 PRÓXIMOS PASSOS RECOMENDADOS")
    print("-" * 30)
    print("1. 🔧 Aplicar middleware ApiResponseMiddleware no main.py")
    print("2. 📝 Migrar endpoints de alta prioridade primeiro")
    print("3. 🧪 Testar cada endpoint migrado")
    print("4. 📚 Atualizar documentação da API")
    print("5. ✅ Validar que todos seguem padrão {success, data, error}")
    
    return report


if __name__ == "__main__":
    report = main()
    
    # Exemplo de aplicação automática (descomentarr se quiser aplicar)
    # print("\n🔄 Aplicando migrações automáticas...")
    # apply_automatic_migrations(report)
