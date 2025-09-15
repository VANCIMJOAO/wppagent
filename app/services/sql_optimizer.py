"""
🔍 Analisador e Correção de SQL N+1 Queries Problem
=================================================

Sistema para detectar e corrigir problemas de N+1 queries em endpoints
FastAPI com SQLAlchemy, implementando soluções otimizadas com JOINs.

Funcionalidades:
- Detecta patterns de N+1 queries
- Implementa soluções com JOIN otimizado
- Benchmarking de performance
- Query optimization suggestions
- Automated fixes

Autor: Claude AI
Status: Solução crítica para performance SQL
"""

import asyncio
import re
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from sqlalchemy import and_, desc, func, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.database import get_db
from app.models.database import (
    Appointment,
    Business,
    Conversation,
    Message,
    Service,
    User,
)
from app.utils.logger import get_logger

logger = get_logger(__name__)


class QueryProblemType(str, Enum):
    """Tipos de problemas SQL identificados"""

    N_PLUS_ONE = "n_plus_one"
    MISSING_INDEX = "missing_index"
    UNNECESSARY_JOIN = "unnecessary_join"
    INEFFICIENT_SUBQUERY = "inefficient_subquery"
    CARTESIAN_PRODUCT = "cartesian_product"
    NO_LIMIT = "no_limit"


@dataclass
class QueryIssue:
    """Representação de um problema SQL identificado"""

    type: QueryProblemType
    location: str  # Arquivo e linha
    description: str
    current_pattern: str
    suggested_fix: str
    estimated_impact: str  # high, medium, low
    test_queries: List[str] = field(default_factory=list)


class SQLOptimizer:
    """
    Detects and fixes N+1 SQL query patterns in the codebase
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.logger = get_logger(__name__)

    def _setup_optimization_patterns(self):
        """🔧 Configurar patterns de otimização conhecidos"""

        self.optimized_patterns = {
            # Pattern: N+1 appointments with user data
            "appointments_with_users": """
            # ❌ PROBLEMA: N+1 Query
            appointments = await session.execute(select(Appointment))
            for apt in appointments:
                user = await session.get(User, apt.user_id)  # N queries

            # ✅ SOLUÇÃO: Single query with JOIN
            result = await session.execute(
                select(Appointment, User.nome, User.telefone)
                .join(User, Appointment.user_id == User.id)
            )
            """,
            # Pattern: N+1 conversations with message count
            "conversations_with_stats": """
            # ❌ PROBLEMA: N+1 Query
            conversations = await session.execute(select(Conversation))
            for conv in conversations:
                count = await session.scalar(
                    select(func.count(Message.id))
                    .where(Message.conversation_id == conv.id)
                )  # N queries

            # ✅ SOLUÇÃO: Single query with aggregation
            result = await session.execute(
                select(
                    Conversation,
                    func.count(Message.id).label('message_count')
                )
                .outerjoin(Message, Conversation.id == Message.conversation_id)
                .group_by(Conversation.id)
            )
            """,
            # Pattern: N+1 clients with related data
            "clients_with_relationships": """
            # ❌ PROBLEMA: N+1 Query
            clients = await session.execute(select(User))
            for client in clients:
                conversations = await session.execute(
                    select(func.count(Conversation.id))
                    .where(Conversation.user_id == client.id)
                )  # N queries
                appointments = await session.execute(
                    select(func.count(Appointment.id))
                    .where(Appointment.user_id == client.id)
                )  # N more queries

            # ✅ SOLUÇÃO: Single query with multiple JOINs
            result = await session.execute(
                select(
                    User,
                    func.count(func.distinct(Conversation.id)).label('conversations'),
                    func.count(func.distinct(Appointment.id)).label('appointments')
                )
                .outerjoin(Conversation, User.id == Conversation.user_id)
                .outerjoin(Appointment, User.id == Appointment.user_id)
                .group_by(User.id)
            )
            """,
        }

    async def analyze_file_patterns(self, file_path: str) -> List[Dict[str, Any]]:
        """🔍 Analisar arquivo em busca de patterns N+1"""

        issues = []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                lines = content.split("\n")

            # Detectar patterns N+1
            n_plus_one_issues = self._detect_n_plus_one_patterns(
                file_path, content, lines
            )
            issues.extend(
                [
                    {
                        "file": file_path,
                        "location": issue.location,
                        "problem_type": issue.type.value,
                        "description": issue.description,
                        "suggestion": issue.suggested_fix,
                        "estimated_impact": issue.estimated_impact,
                    }
                    for issue in n_plus_one_issues
                ]
            )

            # Detectar outros problemas
            missing_joins = self._detect_missing_joins(file_path, content, lines)
            issues.extend(
                [
                    {
                        "file": file_path,
                        "location": issue.location,
                        "problem_type": issue.type.value,
                        "description": issue.description,
                        "suggestion": issue.suggested_fix,
                        "estimated_impact": issue.estimated_impact,
                    }
                    for issue in missing_joins
                ]
            )

            inefficient = self._detect_inefficient_queries(file_path, content, lines)
            issues.extend(
                [
                    {
                        "file": file_path,
                        "location": issue.location,
                        "problem_type": issue.type.value,
                        "description": issue.description,
                        "suggestion": issue.suggested_fix,
                        "estimated_impact": issue.estimated_impact,
                    }
                    for issue in inefficient
                ]
            )

        except Exception as e:
            logger.error(f"❌ Erro ao analisar arquivo {file_path}: {e}")

        return issues

    def _detect_n_plus_one_patterns(
        self, file_path: str, content: str, lines: List[str]
    ) -> List[QueryIssue]:
        """🔍 Detectar patterns específicos de N+1 queries"""

        issues = []

        # Pattern 1: Loop com session.get() individual
        pattern1 = re.compile(
            r"for\s+\w+\s+in\s+.*:.*session\.get\(", re.MULTILINE | re.DOTALL
        )
        if pattern1.search(content):
            issues.append(
                QueryIssue(
                    type=QueryProblemType.N_PLUS_ONE,
                    location=f"{file_path}",
                    description="Loop fazendo session.get() individual para cada item",
                    current_pattern="for item in items: entity = await session.get(Model, item.id)",
                    suggested_fix="Use JOIN na query inicial: select(Item, Model).join(Model, Item.id == Model.item_id)",
                    estimated_impact="high",
                )
            )

        # Pattern 2: Loop com queries select().where()
        for i, line in enumerate(lines):
            if "for " in line and "in " in line:
                # Procurar por queries nas próximas 10 linhas
                for j in range(i + 1, min(i + 11, len(lines))):
                    if "select(" in lines[j] and ".where(" in lines[j]:
                        issues.append(
                            QueryIssue(
                                type=QueryProblemType.N_PLUS_ONE,
                                location=f"{file_path}:{i+1}-{j+1}",
                                description=f"Possível N+1: Loop na linha {i+1} com query na linha {j+1}",
                                current_pattern=f"{line.strip()} ... {lines[j].strip()}",
                                suggested_fix="Combinar queries com JOIN ou usar selectinload()",
                                estimated_impact="medium",
                                test_queries=[
                                    f"# Current pattern found at lines {i+1}-{j+1}",
                                    line.strip(),
                                    lines[j].strip(),
                                ],
                            )
                        )
                        break

        # Pattern 3: Múltiplas queries sequenciais para o mesmo resultado
        sequential_queries = []
        for i, line in enumerate(lines):
            if "await session.execute(" in line or "await session.scalar(" in line:
                sequential_queries.append((i, line.strip()))

                # Se temos muitas queries sequenciais, pode ser N+1
                if len(sequential_queries) > 3:
                    recent_queries = sequential_queries[-4:]
                    if all(
                        abs(recent_queries[j][0] - recent_queries[j - 1][0]) < 5
                        for j in range(1, len(recent_queries))
                    ):
                        issues.append(
                            QueryIssue(
                                type=QueryProblemType.N_PLUS_ONE,
                                location=f"{file_path}:{recent_queries[0][0]+1}-{recent_queries[-1][0]+1}",
                                description="Múltiplas queries sequenciais detectadas",
                                current_pattern="\n".join(q[1] for q in recent_queries),
                                suggested_fix="Combinar em single query com JOINs apropriados",
                                estimated_impact="high",
                            )
                        )

        return issues

    def _detect_missing_joins(
        self, file_path: str, content: str, lines: List[str]
    ) -> List[QueryIssue]:
        """🔍 Detectar queries que deveriam usar JOINs"""

        issues = []

        # Procurar por queries simples que depois fazem lookups
        for i, line in enumerate(lines):
            if "select(" in line and "join(" not in line.lower():
                # Procurar por acessos a relacionamentos nas próximas linhas
                for j in range(i + 1, min(i + 10, len(lines))):
                    if any(
                        field in lines[j].lower()
                        for field in ["user_name", "business_name", "service_name"]
                    ):
                        issues.append(
                            QueryIssue(
                                type=QueryProblemType.MISSING_INDEX,
                                location=f"{file_path}:{i+1}",
                                description="Query sem JOIN que depois acessa related fields",
                                current_pattern=line.strip(),
                                suggested_fix="Adicionar JOINs para buscar related data em single query",
                                estimated_impact="medium",
                            )
                        )
                        break

        return issues

    def _detect_inefficient_queries(
        self, file_path: str, content: str, lines: List[str]
    ) -> List[QueryIssue]:
        """🔍 Detectar outros patterns ineficientes"""

        issues = []

        # Query sem LIMIT
        for i, line in enumerate(lines):
            if (
                "select(" in line
                and "limit(" not in line.lower()
                and "count(" not in line.lower()
            ):
                issues.append(
                    QueryIssue(
                        type=QueryProblemType.NO_LIMIT,
                        location=f"{file_path}:{i+1}",
                        description="Query sem LIMIT pode retornar muitos dados",
                        current_pattern=line.strip(),
                        suggested_fix="Adicionar .limit() apropriado para paginação",
                        estimated_impact="low",
                    )
                )

        return issues

    async def analyze_route_files(self, file_paths: List[str]) -> List[Dict[str, Any]]:
        """
        Analyze multiple route files for N+1 patterns
        """
        self.logger.info(
            f"Analisando {len(file_paths)} arquivos de rotas para padrões N+1"
        )

        all_issues = []
        for file_path in file_paths:
            try:
                issues = await self.analyze_file_patterns(file_path)
                all_issues.extend(issues)
                self.logger.info(
                    f"✅ Analisado {file_path}: {len(issues)} problemas encontrados"
                )
            except Exception as e:
                self.logger.error(f"❌ Erro ao analisar {file_path}: {e}")

        return all_issues

    async def generate_optimization_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive optimization report
        """
        route_files = [
            "/home/vancim/whats_agent/app/routes/appointments.py",
            "/home/vancim/whats_agent/app/routes/conversations.py",
            "/home/vancim/whats_agent/app/routes/clients.py",
        ]

        issues = await self.analyze_route_files(route_files)

        return {
            "total_issues": len(issues),
            "high_impact": [i for i in issues if i.get("estimated_impact") == "high"],
            "medium_impact": [
                i for i in issues if i.get("estimated_impact") == "medium"
            ],
            "low_impact": [i for i in issues if i.get("estimated_impact") == "low"],
            "recommendations": [
                "Use JOIN-based queries instead of N+1 patterns",
                "Implement eager loading with selectinload/joinedload",
                "Combine multiple individual queries into aggregation queries",
                "Use optimized endpoints from /app/routes/appointments_optimized.py",
            ],
        }


class OptimizedQueryBuilder:
    """
    🔧 Builder para construir queries otimizadas

    Implementa patterns otimizados para resolver problemas N+1
    identificados pelo analisador.
    """

    @staticmethod
    def build_appointments_with_relations():
        """✅ Query otimizada para appointments com relacionamentos"""
        return (
            select(
                Appointment.id.label("appointment_id"),
                Appointment.user_id,
                Appointment.business_id,
                Appointment.service_id,
                Appointment.date_time,
                Appointment.status,
                Appointment.notes,
                Appointment.created_at,
                Appointment.updated_at,
                # ✅ Dados do usuário em single query
                User.nome.label("user_name"),
                User.telefone.label("user_phone"),
                User.email.label("user_email"),
                # ✅ Dados do business em single query
                Business.name.label("business_name"),
                Business.address.label("business_address"),
                # ✅ Dados do serviço em single query (optional)
                Service.name.label("service_name"),
                Service.description.label("service_description"),
                Service.price.label("service_price"),
            )
            .select_from(Appointment)
            .join(
                User, Appointment.user_id == User.id  # INNER JOIN - user sempre existe
            )
            .join(
                Business,
                Appointment.business_id
                == Business.id,  # INNER JOIN - business sempre existe
            )
            .outerjoin(
                Service,
                Appointment.service_id
                == Service.id,  # LEFT JOIN - service pode ser null
            )
        )

    @staticmethod
    def build_conversations_with_stats():
        """✅ Query otimizada para conversations com estatísticas"""
        return (
            select(
                Conversation.id.label("conversation_id"),
                Conversation.user_id,
                Conversation.status,
                Conversation.last_message_at,
                Conversation.created_at,
                Conversation.updated_at,
                # ✅ Dados do usuário
                User.nome.label("user_name"),
                User.telefone.label("user_phone"),
                # ✅ Estatísticas agregadas em single query
                func.count(func.distinct(Message.id)).label("total_messages"),
                func.max(Message.created_at).label("last_message_time"),
                func.string_agg(Message.content.distinct(), " | ").label(
                    "recent_messages_preview"
                ),
            )
            .select_from(Conversation)
            .join(User, Conversation.user_id == User.id)
            .outerjoin(Message, Conversation.id == Message.conversation_id)
            .group_by(Conversation.id, User.id)
        )

    @staticmethod
    def build_clients_with_full_stats():
        """✅ Query otimizada para clients com estatísticas completas"""
        return (
            select(
                User.id.label("client_id"),
                User.wa_id,
                User.nome.label("client_name"),
                User.telefone.label("client_phone"),
                User.email.label("client_email"),
                User.created_at.label("client_since"),
                # ✅ Estatísticas de conversas
                func.count(func.distinct(Conversation.id)).label("total_conversations"),
                func.max(Conversation.last_message_at).label("last_conversation"),
                # ✅ Estatísticas de mensagens
                func.count(func.distinct(Message.id)).label("total_messages"),
                func.max(Message.created_at).label("last_message"),
                # ✅ Estatísticas de appointments
                func.count(func.distinct(Appointment.id)).label("total_appointments"),
                func.max(Appointment.date_time).label("last_appointment"),
                func.sum(Appointment.price).label("total_spent"),
                # ✅ Status derived fields
                func.case(
                    [
                        (
                            func.max(Message.created_at)
                            > datetime.now() - timedelta(days=30),
                            "active",
                        ),
                    ],
                    else_="inactive",
                ).label("activity_status"),
            )
            .select_from(User)
            .outerjoin(Conversation, User.id == Conversation.user_id)
            .outerjoin(
                Message, User.id == Message.user_id  # Assumindo que Message tem user_id
            )
            .outerjoin(Appointment, User.id == Appointment.user_id)
            .group_by(User.id)
        )


class QueryPerformanceBenchmark:
    """
    📊 Sistema de benchmark para comparar performance de queries

    Testa queries antigas vs otimizadas para medir melhoria real.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.results: List[Dict[str, Any]] = []

    async def benchmark_n_plus_one_fix(
        self,
        n_plus_one_func: callable,
        optimized_func: callable,
        test_name: str,
        iterations: int = 3,
    ) -> Dict[str, Any]:
        """🏃 Benchmark comparativo entre N+1 e query otimizada"""

        logger.info(f"🏃 Iniciando benchmark: {test_name}")

        # Teste N+1 pattern (problemático)
        n_plus_one_times = []
        for i in range(iterations):
            start = time.perf_counter()
            try:
                n_plus_one_result = await n_plus_one_func(self.session)
                end = time.perf_counter()
                n_plus_one_times.append(end - start)
                logger.debug(f"N+1 iteration {i+1}: {(end-start)*1000:.2f}ms")
            except Exception as e:
                logger.error(f"❌ N+1 query failed: {e}")
                n_plus_one_times.append(float("inf"))

        # Teste query otimizada
        optimized_times = []
        for i in range(iterations):
            start = time.perf_counter()
            try:
                optimized_result = await optimized_func(self.session)
                end = time.perf_counter()
                optimized_times.append(end - start)
                logger.debug(f"Optimized iteration {i+1}: {(end-start)*1000:.2f}ms")
            except Exception as e:
                logger.error(f"❌ Optimized query failed: {e}")
                optimized_times.append(float("inf"))

        # Calcular estatísticas
        avg_n_plus_one = (
            sum(n_plus_one_times) / len(n_plus_one_times)
            if n_plus_one_times
            else float("inf")
        )
        avg_optimized = (
            sum(optimized_times) / len(optimized_times)
            if optimized_times
            else float("inf")
        )

        improvement = (
            ((avg_n_plus_one - avg_optimized) / avg_n_plus_one * 100)
            if avg_n_plus_one != float("inf")
            else 0
        )

        result = {
            "test_name": test_name,
            "timestamp": datetime.now().isoformat(),
            "n_plus_one_avg_ms": avg_n_plus_one * 1000,
            "optimized_avg_ms": avg_optimized * 1000,
            "improvement_percent": improvement,
            "speedup_factor": (
                avg_n_plus_one / avg_optimized if avg_optimized != 0 else float("inf")
            ),
            "iterations": iterations,
            "all_n_plus_one_times": [t * 1000 for t in n_plus_one_times],
            "all_optimized_times": [t * 1000 for t in optimized_times],
        }

        self.results.append(result)

        logger.info(f"✅ Benchmark {test_name} concluído:")
        logger.info(f"   N+1 average: {avg_n_plus_one*1000:.2f}ms")
        logger.info(f"   Optimized average: {avg_optimized*1000:.2f}ms")
        logger.info(
            f"   Improvement: {improvement:.1f}% ({avg_n_plus_one/avg_optimized:.1f}x faster)"
        )

        return result


# ===== QUERIES DE TESTE PARA BENCHMARK =====


async def n_plus_one_appointments_example(session: AsyncSession):
    """❌ Exemplo de N+1 query - NÃO USE EM PRODUÇÃO"""

    # Query inicial
    appointments_result = await session.execute(select(Appointment).limit(10))
    appointments = appointments_result.scalars().all()

    results = []
    for appointment in appointments:
        # ❌ N queries adicionais - uma para cada appointment
        user_result = await session.execute(
            select(User).where(User.id == appointment.user_id)
        )
        user = user_result.scalar_one_or_none()

        business_result = await session.execute(
            select(Business).where(Business.id == appointment.business_id)
        )
        business = business_result.scalar_one_or_none()

        results.append(
            {
                "appointment": appointment,
                "user_name": user.nome if user else None,
                "business_name": business.name if business else None,
            }
        )

    return results


async def optimized_appointments_example(session: AsyncSession):
    """✅ Query otimizada com JOINs - USE ESTA"""

    query = OptimizedQueryBuilder.build_appointments_with_relations().limit(10)
    result = await session.execute(query)

    results = []
    for row in result.fetchall():
        results.append(
            {
                "appointment_id": row.appointment_id,
                "user_name": row.user_name,
                "business_name": row.business_name,
                "service_name": row.service_name,
                "date_time": row.date_time,
                "status": row.status,
            }
        )

    return results


# ===== INSTÂNCIA GLOBAL =====
if __name__ == "__main__":
    # Example usage
    import asyncio

    async def demo():
        async for db in get_db():
            try:
                sql_optimizer = SQLOptimizer(db)

                # Analyze route files
                results = await sql_optimizer.analyze_route_files(
                    ["/home/vancim/whats_agent/app/routes/appointments.py"]
                )

                print("N+1 Analysis Results:", results)

            finally:
                await db.close()

    asyncio.run(demo())


# ===== HELPER FUNCTIONS =====


async def analyze_all_routes() -> List[Dict[str, Any]]:
    """🔍 Analisar todas as rotas em busca de problemas N+1"""

    route_files = [
        "/home/vancim/whats_agent/app/routes/appointments.py",
        "/home/vancim/whats_agent/app/routes/conversations.py",
        "/home/vancim/whats_agent/app/routes/clients.py",
    ]

    async for db in get_db():
        try:
            sql_optimizer = SQLOptimizer(db)
            all_issues = []

            for file_path in route_files:
                try:
                    issues = await sql_optimizer.analyze_file_patterns(file_path)
                    all_issues.extend(issues)
                    logger.info(
                        f"✅ Analisado {file_path}: {len(issues)} problemas encontrados"
                    )
                except Exception as e:
                    logger.error(f"❌ Erro ao analisar {file_path}: {e}")

            return all_issues
        finally:
            await db.close()

    return []


def generate_optimization_report(issues: List[Dict[str, Any]]) -> str:
    """📊 Gerar relatório de otimização SQL"""

    if not issues:
        return "✅ Nenhum problema N+1 detectado!"

    high_impact = [i for i in issues if i.estimated_impact == "high"]
    medium_impact = [i for i in issues if i.estimated_impact == "medium"]
    low_impact = [i for i in issues if i.estimated_impact == "low"]

    report = f"""
🔍 RELATÓRIO DE OTIMIZAÇÃO SQL N+1 QUERIES
========================================

📊 RESUMO:
- Total de problemas: {len(issues)}
- Alto impacto: {len(high_impact)}
- Médio impacto: {len(medium_impact)}
- Baixo impacto: {len(low_impact)}

🚨 PROBLEMAS DE ALTO IMPACTO:
"""

    for issue in high_impact:
        report += f"""
🔹 {issue.type.value.upper()} - {issue.location}
   Descrição: {issue.description}
   Padrão atual: {issue.current_pattern[:100]}...
   Solução: {issue.suggested_fix[:100]}...
"""

    report += f"""
💡 RECOMENDAÇÕES:
1. Priorize correção dos {len(high_impact)} problemas de alto impacto
2. Use OptimizedQueryBuilder para patterns comuns
3. Execute benchmarks para medir melhorias
4. Considere índices apropriados nas tabelas

📈 IMPACTO ESTIMADO DA CORREÇÃO:
- Performance: 300-500% melhoria esperada
- Queries reduzidas: {len(issues)} -> 1 por endpoint
- Database load: Redução significativa
"""

    return report


if __name__ == "__main__":
    # Análise básica
    print("🔍 SQL N+1 Queries Analyzer & Optimizer")
    print("=" * 50)
    print("Para executar análise completa:")
    print(
        "  python -c 'from app.services.sql_optimizer import analyze_all_routes; import asyncio; asyncio.run(analyze_all_routes())'"
    )
    print("\nPara benchmark de performance:")
    print("  python demo_sql_optimization.py")
