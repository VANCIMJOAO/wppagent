#!/usr/bin/env python3
"""
TRILHA 2 FASE 3 - Log Analytics
Sistema de análise automatizada de logs com pattern recognition
"""

import asyncio
import gzip
import hashlib
import json
import os
import re
import statistics
import threading
import time
from collections import Counter, defaultdict, deque
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple


class LogLevel(Enum):
    """Níveis de log"""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class PatternType(Enum):
    """Tipos de padrão"""

    ERROR_PATTERN = "error"
    WARNING_PATTERN = "warning"
    PERFORMANCE_PATTERN = "performance"
    SECURITY_PATTERN = "security"
    CUSTOM_PATTERN = "custom"


@dataclass
class LogEntry:
    """Entrada de log estruturada"""

    timestamp: float
    level: LogLevel
    message: str
    source: str  # arquivo, serviço, etc.
    raw_line: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    extracted_fields: Dict[str, str] = field(default_factory=dict)

    def get_datetime(self) -> datetime:
        """Converte timestamp para datetime"""
        return datetime.fromtimestamp(self.timestamp)

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário"""
        return {
            "timestamp": self.timestamp,
            "datetime": self.get_datetime().isoformat(),
            "level": self.level.value,
            "message": self.message,
            "source": self.source,
            "metadata": self.metadata,
            "extracted_fields": self.extracted_fields,
        }


@dataclass
class LogPattern:
    """Padrão de log"""

    name: str
    regex: str
    pattern_type: PatternType
    severity: int  # 1-10
    description: str
    extract_fields: List[str] = field(default_factory=list)
    action: Optional[str] = None
    enabled: bool = True

    def __post_init__(self):
        self.compiled_regex = re.compile(self.regex, re.IGNORECASE)

    def match(self, log_entry: LogEntry) -> Optional[Dict[str, str]]:
        """Verifica se o padrão corresponde ao log"""
        if not self.enabled:
            return None

        match = self.compiled_regex.search(log_entry.message)
        if match:
            extracted = {}
            for i, field_name in enumerate(self.extract_fields):
                try:
                    extracted[field_name] = match.group(i + 1)
                except IndexError:
                    pass
            return extracted
        return None


@dataclass
class LogAlert:
    """Alerta baseado em logs"""

    pattern_name: str
    count: int
    time_window: int
    first_occurrence: float
    last_occurrence: float
    severity: int
    samples: List[LogEntry] = field(default_factory=list)

    def get_rate(self) -> float:
        """Obtém taxa de ocorrência por minuto"""
        duration = max(self.last_occurrence - self.first_occurrence, 1)
        return (self.count / duration) * 60


@dataclass
class LogInsight:
    """Insight extraído dos logs"""

    type: str
    title: str
    description: str
    severity: int
    evidence: List[str]
    recommendations: List[str]
    confidence: float
    timestamp: float = field(default_factory=time.time)


class LogProcessor:
    """Processador de logs"""

    def __init__(self):
        self.patterns: Dict[str, LogPattern] = {}
        self.common_parsers = self._setup_common_parsers()

    def _setup_common_parsers(self) -> Dict[str, re.Pattern]:
        """Configura parsers comuns de logs"""
        return {
            "timestamp": re.compile(r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}"),
            "ip_address": re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
            "email": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),
            "url": re.compile(r"https?://[^\s]+"),
            "json": re.compile(r"\{.*\}"),
            "error_code": re.compile(r"[4-5]\d{2}"),
            "duration": re.compile(
                r"\d+\.?\d*\s?(ms|s|sec|seconds?|minutes?|min|hours?|h)"
            ),
        }

    def parse_log_line(self, line: str, source: str = "unknown") -> Optional[LogEntry]:
        """Parse uma linha de log"""
        line = line.strip()
        if not line:
            return None

        # Extrair timestamp
        timestamp = self._extract_timestamp(line)

        # Extrair nível de log
        level = self._extract_log_level(line)

        # Extrair mensagem (remover timestamp e level)
        message = self._extract_message(line)

        # Extrair campos comuns
        extracted_fields = self._extract_common_fields(message)

        entry = LogEntry(
            timestamp=timestamp,
            level=level,
            message=message,
            source=source,
            raw_line=line,
            extracted_fields=extracted_fields,
        )

        return entry

    def _extract_timestamp(self, line: str) -> float:
        """Extrai timestamp da linha"""
        timestamp_match = self.common_parsers["timestamp"].search(line)
        if timestamp_match:
            timestamp_str = timestamp_match.group()
            try:
                # Tentar diferentes formatos
                formats = [
                    "%Y-%m-%d %H:%M:%S",
                    "%Y-%m-%dT%H:%M:%S",
                    "%Y-%m-%d %H:%M:%S.%f",
                    "%Y-%m-%dT%H:%M:%S.%f",
                ]

                for fmt in formats:
                    try:
                        dt = datetime.strptime(
                            timestamp_str[: len(fmt.replace(".%f", ""))],
                            fmt.replace(".%f", ""),
                        )
                        return dt.timestamp()
                    except ValueError:
                        continue
            except:
                pass

        # Se não conseguir extrair, usar timestamp atual
        return time.time()

    def _extract_log_level(self, line: str) -> LogLevel:
        """Extrai nível de log"""
        line_upper = line.upper()
        for level in LogLevel:
            if level.value in line_upper:
                return level

        # Inferir nível baseado em palavras-chave
        if any(
            keyword in line_upper for keyword in ["ERROR", "FAIL", "EXCEPTION", "CRASH"]
        ):
            return LogLevel.ERROR
        elif any(keyword in line_upper for keyword in ["WARN", "WARNING"]):
            return LogLevel.WARNING
        elif any(keyword in line_upper for keyword in ["CRITICAL", "FATAL", "SEVERE"]):
            return LogLevel.CRITICAL
        else:
            return LogLevel.INFO

    def _extract_message(self, line: str) -> str:
        """Extrai mensagem limpa"""
        # Remove timestamp e level comum
        cleaned = re.sub(r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}[\.\d]*", "", line)
        cleaned = re.sub(
            r"\b(DEBUG|INFO|WARNING|ERROR|CRITICAL)\b", "", cleaned, flags=re.IGNORECASE
        )
        return cleaned.strip()

    def _extract_common_fields(self, message: str) -> Dict[str, str]:
        """Extrai campos comuns da mensagem"""
        fields = {}

        for field_name, pattern in self.common_parsers.items():
            match = pattern.search(message)
            if match:
                fields[field_name] = match.group()

        return fields

    def add_pattern(self, pattern: LogPattern):
        """Adiciona padrão de detecção"""
        self.patterns[pattern.name] = pattern

    def analyze_entry(self, entry: LogEntry) -> List[Tuple[str, Dict[str, str]]]:
        """Analisa entrada contra todos os padrões"""
        matches = []
        for pattern_name, pattern in self.patterns.items():
            extracted = pattern.match(entry)
            if extracted is not None:
                matches.append((pattern_name, extracted))
                entry.extracted_fields.update(extracted)
        return matches


class LogAggregator:
    """Agregador de logs"""

    def __init__(self, retention_hours: int = 24):
        self.retention_hours = retention_hours
        self.entries: deque = deque()
        self.pattern_counts: Dict[str, int] = defaultdict(int)
        self.level_counts: Dict[str, int] = defaultdict(int)
        self.source_counts: Dict[str, int] = defaultdict(int)
        self.hourly_counts: Dict[int, int] = defaultdict(int)
        self.error_trend: deque = deque(maxlen=60)  # últimos 60 minutos

    def add_entry(self, entry: LogEntry):
        """Adiciona entrada e atualiza agregações"""
        self.entries.append(entry)
        self.level_counts[entry.level.value] += 1
        self.source_counts[entry.source] += 1

        # Contagem por hora
        hour = int(entry.timestamp // 3600)
        self.hourly_counts[hour] += 1

        # Tendência de erros
        if entry.level in [LogLevel.ERROR, LogLevel.CRITICAL]:
            minute = int(entry.timestamp // 60)
            self.error_trend.append(minute)

        # Limpar entradas antigas
        self._cleanup_old_entries()

    def _cleanup_old_entries(self):
        """Remove entradas antigas"""
        cutoff_time = time.time() - (self.retention_hours * 3600)
        while self.entries and self.entries[0].timestamp < cutoff_time:
            old_entry = self.entries.popleft()
            self.level_counts[old_entry.level.value] -= 1
            self.source_counts[old_entry.source] -= 1

    def get_stats(self) -> Dict[str, Any]:
        """Obtém estatísticas agregadas"""
        total_entries = len(self.entries)

        if total_entries == 0:
            return {"total": 0}

        # Calcular timespan
        oldest = self.entries[0].timestamp
        newest = self.entries[-1].timestamp
        timespan_hours = (newest - oldest) / 3600

        # Calcular taxa de erros
        error_count = self.level_counts.get("ERROR", 0) + self.level_counts.get(
            "CRITICAL", 0
        )
        error_rate = (error_count / total_entries) * 100 if total_entries > 0 else 0

        # Tendência de erros (últimos 60 minutos)
        current_minute = int(time.time() // 60)
        recent_errors = sum(
            1 for minute in self.error_trend if current_minute - minute <= 60
        )

        return {
            "total": total_entries,
            "timespan_hours": timespan_hours,
            "entries_per_hour": total_entries / max(timespan_hours, 1),
            "error_rate_percent": error_rate,
            "recent_errors": recent_errors,
            "levels": dict(self.level_counts),
            "sources": dict(self.source_counts),
            "top_sources": sorted(
                self.source_counts.items(), key=lambda x: x[1], reverse=True
            )[:5],
        }

    def search(self, query: str, max_results: int = 100) -> List[LogEntry]:
        """Busca logs por query"""
        query_lower = query.lower()
        results = []

        for entry in reversed(self.entries):  # Mais recentes primeiro
            if (
                query_lower in entry.message.lower()
                or query_lower in entry.source.lower()
                or any(
                    query_lower in str(v).lower()
                    for v in entry.extracted_fields.values()
                )
            ):
                results.append(entry)
                if len(results) >= max_results:
                    break

        return results


class InsightEngine:
    """Motor de insights automáticos"""

    def __init__(self, aggregator: LogAggregator):
        self.aggregator = aggregator
        self.insights: List[LogInsight] = []
        self.analysis_cache: Dict[str, Any] = {}

    def generate_insights(self) -> List[LogInsight]:
        """Gera insights automáticos"""
        self.insights.clear()

        # Análise de tendências de erro
        self._analyze_error_trends()

        # Análise de padrões de performance
        self._analyze_performance_patterns()

        # Análise de segurança
        self._analyze_security_patterns()

        # Análise de fontes problemáticas
        self._analyze_problematic_sources()

        # Análise temporal
        self._analyze_temporal_patterns()

        return sorted(self.insights, key=lambda x: x.severity, reverse=True)

    def _analyze_error_trends(self):
        """Analisa tendências de erro"""
        stats = self.aggregator.get_stats()

        if stats["total"] == 0:
            return

        error_rate = stats["error_rate_percent"]
        recent_errors = stats["recent_errors"]

        if error_rate > 10:
            self.insights.append(
                LogInsight(
                    type="error_trend",
                    title="Alta Taxa de Erros",
                    description=f"Taxa de erros está em {error_rate:.1f}% (acima do normal)",
                    severity=8 if error_rate > 20 else 6,
                    evidence=[
                        f"Taxa de erros: {error_rate:.1f}%",
                        f"Erros recentes: {recent_errors}",
                    ],
                    recommendations=[
                        "Investigar logs de erro mais recentes",
                        "Verificar saúde dos serviços",
                        "Considerar rollback se necessário",
                    ],
                    confidence=0.9,
                )
            )

        if recent_errors > 10:
            self.insights.append(
                LogInsight(
                    type="error_spike",
                    title="Pico de Erros Recente",
                    description=f"Detectados {recent_errors} erros na última hora",
                    severity=7,
                    evidence=[f"Erros na última hora: {recent_errors}"],
                    recommendations=[
                        "Verificar alertas de monitoramento",
                        "Analisar logs de sistema",
                        "Verificar recursos do servidor",
                    ],
                    confidence=0.8,
                )
            )

    def _analyze_performance_patterns(self):
        """Analisa padrões de performance"""
        # Buscar logs com duração
        slow_requests = []
        for entry in self.aggregator.entries:
            if "duration" in entry.extracted_fields:
                duration_str = entry.extracted_fields["duration"]
                try:
                    # Extrair valor numérico
                    duration_match = re.search(r"(\d+\.?\d*)", duration_str)
                    if duration_match:
                        duration = float(duration_match.group(1))
                        if "ms" in duration_str and duration > 1000:  # > 1s
                            slow_requests.append((entry, duration))
                        elif "s" in duration_str and duration > 5:  # > 5s
                            slow_requests.append((entry, duration))
                except:
                    pass

        if len(slow_requests) > 5:
            avg_duration = statistics.mean([d for _, d in slow_requests])
            self.insights.append(
                LogInsight(
                    type="performance",
                    title="Requisições Lentas Detectadas",
                    description=f"Encontradas {len(slow_requests)} requisições lentas (média: {avg_duration:.1f})",
                    severity=6,
                    evidence=[
                        f"Requisições lentas: {len(slow_requests)}",
                        f"Duração média: {avg_duration:.1f}",
                    ],
                    recommendations=[
                        "Investigar bottlenecks de performance",
                        "Verificar queries de banco de dados",
                        "Analisar uso de CPU e memória",
                    ],
                    confidence=0.7,
                )
            )

    def _analyze_security_patterns(self):
        """Analisa padrões de segurança"""
        security_keywords = [
            "unauthorized",
            "forbidden",
            "attack",
            "intrusion",
            "malicious",
            "suspicious",
        ]
        security_logs = []

        for entry in self.aggregator.entries:
            message_lower = entry.message.lower()
            if any(keyword in message_lower for keyword in security_keywords):
                security_logs.append(entry)

        if len(security_logs) > 3:
            self.insights.append(
                LogInsight(
                    type="security",
                    title="Atividade de Segurança Suspeita",
                    description=f"Detectados {len(security_logs)} eventos de segurança",
                    severity=9,
                    evidence=[f"Eventos de segurança: {len(security_logs)}"],
                    recommendations=[
                        "Revisar logs de segurança imediatamente",
                        "Verificar tentativas de acesso não autorizado",
                        "Considerar bloqueio de IPs suspeitos",
                    ],
                    confidence=0.8,
                )
            )

    def _analyze_problematic_sources(self):
        """Analisa fontes problemáticas"""
        stats = self.aggregator.get_stats()
        top_sources = stats.get("top_sources", [])

        for source, count in top_sources:
            if count > 100:  # Muitos logs de uma fonte
                # Verificar se tem muitos erros
                source_errors = sum(
                    1
                    for entry in self.aggregator.entries
                    if entry.source == source
                    and entry.level in [LogLevel.ERROR, LogLevel.CRITICAL]
                )

                if source_errors > count * 0.1:  # > 10% de erros
                    self.insights.append(
                        LogInsight(
                            type="source_analysis",
                            title=f"Fonte Problemática: {source}",
                            description=f"Alta atividade com {source_errors} erros em {count} logs",
                            severity=7,
                            evidence=[
                                f"Total de logs: {count}",
                                f"Erros: {source_errors}",
                            ],
                            recommendations=[
                                f"Investigar problemas em {source}",
                                "Verificar configuração do serviço",
                                "Considerar restart se necessário",
                            ],
                            confidence=0.6,
                        )
                    )

    def _analyze_temporal_patterns(self):
        """Analisa padrões temporais"""
        # Analisar distribuição por hora
        hour_counts = defaultdict(int)
        for entry in self.aggregator.entries:
            hour = datetime.fromtimestamp(entry.timestamp).hour
            hour_counts[hour] += 1

        if hour_counts:
            max_hour = max(hour_counts.values())
            min_hour = min(hour_counts.values())

            if max_hour > min_hour * 3:  # Variação > 3x
                peak_hours = [h for h, c in hour_counts.items() if c == max_hour]
                self.insights.append(
                    LogInsight(
                        type="temporal",
                        title="Padrão de Atividade Irregular",
                        description=f"Picos de atividade detectados em horários específicos",
                        severity=4,
                        evidence=[
                            f"Pico nas horas: {peak_hours}",
                            f"Variação: {max_hour/min_hour:.1f}x",
                        ],
                        recommendations=[
                            "Verificar se os picos são esperados",
                            "Considerar ajuste de recursos",
                            "Analisar padrões de uso",
                        ],
                        confidence=0.5,
                    )
                )


class LogAnalytics:
    """Sistema principal de análise de logs"""

    def __init__(self):
        self.processor = LogProcessor()
        self.aggregator = LogAggregator()
        self.insight_engine = InsightEngine(self.aggregator)
        self.alerts: List[LogAlert] = []
        self.monitoring = False
        self.monitor_task = None

        self._setup_default_patterns()

    def _setup_default_patterns(self):
        """Configura padrões padrão"""
        patterns = [
            LogPattern(
                name="database_error",
                regex=r"database.*error|sql.*error|connection.*timeout",
                pattern_type=PatternType.ERROR_PATTERN,
                severity=8,
                description="Erro de banco de dados",
                extract_fields=["error_type"],
            ),
            LogPattern(
                name="http_error",
                regex=r"HTTP.*([4-5]\d{2})",
                pattern_type=PatternType.ERROR_PATTERN,
                severity=6,
                description="Erro HTTP",
                extract_fields=["status_code"],
            ),
            LogPattern(
                name="memory_error",
                regex=r"out of memory|memory.*full|allocation.*failed",
                pattern_type=PatternType.ERROR_PATTERN,
                severity=9,
                description="Erro de memória",
                extract_fields=[],
            ),
            LogPattern(
                name="slow_query",
                regex=r"slow.*query|query.*took.*(\d+\.?\d*)\s*(ms|s)",
                pattern_type=PatternType.PERFORMANCE_PATTERN,
                severity=5,
                description="Query lenta",
                extract_fields=["duration", "unit"],
            ),
            LogPattern(
                name="authentication_failure",
                regex=r"authentication.*failed|login.*failed|unauthorized",
                pattern_type=PatternType.SECURITY_PATTERN,
                severity=7,
                description="Falha de autenticação",
                extract_fields=[],
            ),
            LogPattern(
                name="webhook_timeout",
                regex=r"webhook.*timeout|webhook.*failed",
                pattern_type=PatternType.ERROR_PATTERN,
                severity=6,
                description="Timeout de webhook",
                extract_fields=[],
            ),
            LogPattern(
                name="ai_processing_error",
                regex=r"ai.*error|openai.*error|llm.*error",
                pattern_type=PatternType.ERROR_PATTERN,
                severity=7,
                description="Erro no processamento de IA",
                extract_fields=[],
            ),
        ]

        for pattern in patterns:
            self.processor.add_pattern(pattern)

    def process_log_file(self, file_path: str) -> int:
        """Processa arquivo de log"""
        if not os.path.exists(file_path):
            return 0

        count = 0
        try:
            if file_path.endswith(".gz"):
                with gzip.open(file_path, "rt", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        entry = self.processor.parse_log_line(
                            line, os.path.basename(file_path)
                        )
                        if entry:
                            self.add_log_entry(entry)
                            count += 1
            else:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        entry = self.processor.parse_log_line(
                            line, os.path.basename(file_path)
                        )
                        if entry:
                            self.add_log_entry(entry)
                            count += 1
        except Exception as e:
            print(f"Error processing {file_path}: {e}")

        return count

    def add_log_entry(self, entry: LogEntry):
        """Adiciona entrada de log"""
        # Analisar contra padrões
        matches = self.processor.analyze_entry(entry)

        # Atualizar contadores de padrões
        for pattern_name, _ in matches:
            self.aggregator.pattern_counts[pattern_name] += 1

        # Adicionar ao agregador
        self.aggregator.add_entry(entry)

    def add_log_line(self, line: str, source: str = "runtime"):
        """Adiciona linha de log em tempo real"""
        entry = self.processor.parse_log_line(line, source)
        if entry:
            self.add_log_entry(entry)

    def search_logs(self, query: str, max_results: int = 100) -> List[LogEntry]:
        """Busca logs"""
        return self.aggregator.search(query, max_results)

    def get_insights(self) -> List[LogInsight]:
        """Obtém insights automáticos"""
        return self.insight_engine.generate_insights()

    def get_dashboard_data(self) -> Dict[str, Any]:
        """Obtém dados para dashboard"""
        stats = self.aggregator.get_stats()
        insights = self.get_insights()

        return {
            "timestamp": time.time(),
            "stats": stats,
            "insights": [
                {
                    "type": insight.type,
                    "title": insight.title,
                    "description": insight.description,
                    "severity": insight.severity,
                    "confidence": insight.confidence,
                    "recommendations": insight.recommendations[:2],  # Primeiras 2
                }
                for insight in insights[:10]  # Top 10
            ],
            "pattern_matches": dict(self.aggregator.pattern_counts),
            "recent_errors": self._get_recent_errors(limit=5),
        }

    def _get_recent_errors(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Obtém erros recentes"""
        errors = []
        for entry in reversed(self.aggregator.entries):
            if entry.level in [LogLevel.ERROR, LogLevel.CRITICAL]:
                errors.append(
                    {
                        "timestamp": entry.timestamp,
                        "datetime": entry.get_datetime().strftime("%H:%M:%S"),
                        "level": entry.level.value,
                        "message": (
                            entry.message[:100] + "..."
                            if len(entry.message) > 100
                            else entry.message
                        ),
                        "source": entry.source,
                    }
                )
                if len(errors) >= limit:
                    break
        return errors

    def generate_report(self) -> str:
        """Gera relatório de análise"""
        stats = self.aggregator.get_stats()
        insights = self.get_insights()

        report = f"""
📊 LOG ANALYTICS REPORT
{'=' * 50}

📈 ESTATÍSTICAS GERAIS:
  Total de Logs: {stats.get('total', 0):,}
  Taxa de Erros: {stats.get('error_rate_percent', 0):.1f}%
  Erros Recentes: {stats.get('recent_errors', 0)}
  Período: {stats.get('timespan_hours', 0):.1f} horas

📋 DISTRIBUIÇÃO POR NÍVEL:
"""

        for level, count in stats.get("levels", {}).items():
            percentage = (count / stats.get("total", 1)) * 100
            report += f"  {level}: {count:,} ({percentage:.1f}%)\n"

        report += f"\n🔍 TOP INSIGHTS ({len(insights)}):\n"
        for i, insight in enumerate(insights[:5], 1):
            severity_emoji = (
                "🔴"
                if insight.severity >= 8
                else "🟡" if insight.severity >= 6 else "🟢"
            )
            report += f"  {i}. {severity_emoji} {insight.title}\n"
            report += f"     {insight.description}\n"
            if insight.recommendations:
                report += f"     💡 {insight.recommendations[0]}\n"
            report += "\n"

        report += f"🏷️ PADRÕES DETECTADOS:\n"
        for pattern, count in sorted(
            self.aggregator.pattern_counts.items(), key=lambda x: x[1], reverse=True
        )[:5]:
            report += f"  {pattern}: {count} ocorrências\n"

        return report


class LogAnalyticsDemo:
    """Demonstração do sistema de análise de logs"""

    def __init__(self):
        self.analytics = LogAnalytics()

    async def run_log_analytics_demo(self):
        """Executa demonstração do sistema"""
        print("📊 TRILHA 2 FASE 3 - Log Analytics Demo")
        print("🔍 Sistema de Análise Automatizada de Logs")
        print("=" * 60)

        # Gerar logs de demonstração
        await self._generate_sample_logs()

        # Processar logs existentes
        await self._process_existing_logs()

        # Demonstrar análise em tempo real
        await self._demo_real_time_analysis()

        # Gerar insights
        await self._demo_insights_generation()

        # Mostrar dashboard
        self._show_dashboard()

        # Gerar relatório final
        self._show_final_report()

        print(f"\n📊 Log Analytics Demo Completed!")
        return True

    async def _generate_sample_logs(self):
        """Gera logs de exemplo"""
        print(f"\n📝 Scenario 1: Generating Sample Logs")
        print("=" * 40)

        sample_logs = [
            "2025-09-15 14:00:01 INFO Starting WhatsApp Agent service",
            "2025-09-15 14:00:05 INFO Database connection established",
            "2025-09-15 14:00:10 INFO Webhook endpoint configured",
            "2025-09-15 14:01:15 WARNING High memory usage detected: 85%",
            "2025-09-15 14:01:30 ERROR Database connection timeout after 30s",
            "2025-09-15 14:02:00 INFO Webhook received from +5511999999999",
            "2025-09-15 14:02:05 ERROR AI processing error: OpenAI timeout",
            "2025-09-15 14:02:10 WARNING Slow query took 2500ms",
            "2025-09-15 14:03:00 CRITICAL Out of memory allocation failed",
            "2025-09-15 14:03:15 ERROR HTTP 500 Internal Server Error",
            "2025-09-15 14:03:30 WARNING Authentication failed for user admin",
            "2025-09-15 14:04:00 INFO Message sent successfully",
            "2025-09-15 14:04:15 ERROR Webhook timeout after 30s",
            "2025-09-15 14:04:30 WARNING Database query took 1800ms",
            "2025-09-15 14:05:00 ERROR AI processing error: Rate limit exceeded",
            "2025-09-15 14:05:15 CRITICAL Database connection pool exhausted",
            "2025-09-15 14:05:30 INFO Service restarted successfully",
            "2025-09-15 14:06:00 WARNING Memory usage still high: 90%",
            "2025-09-15 14:06:15 ERROR HTTP 429 Too Many Requests",
            "2025-09-15 14:06:30 INFO Normal operations resumed",
        ]

        print(f"📝 Adding {len(sample_logs)} sample log entries...")
        for log_line in sample_logs:
            self.analytics.add_log_line(log_line, "whatsapp-agent.log")
            await asyncio.sleep(0.1)  # Simular tempo real

        print(f"✅ Sample logs processed")

    async def _process_existing_logs(self):
        """Processa logs existentes do sistema"""
        print(f"\n📁 Scenario 2: Processing Existing Logs")
        print("=" * 40)

        # Verificar se existem logs no diretório
        log_paths = ["/home/vancim/whats_agent/logs", "/var/log", "."]

        found_logs = False
        for log_dir in log_paths:
            if os.path.exists(log_dir):
                for file_name in os.listdir(log_dir):
                    if file_name.endswith((".log", ".txt")) and os.path.isfile(
                        os.path.join(log_dir, file_name)
                    ):
                        file_path = os.path.join(log_dir, file_name)
                        try:
                            count = self.analytics.process_log_file(file_path)
                            if count > 0:
                                print(f"📁 Processed {file_path}: {count} entries")
                                found_logs = True
                        except Exception as e:
                            print(f"❌ Error processing {file_path}: {e}")

        if not found_logs:
            print(f"ℹ️ No existing log files found in standard locations")

        await asyncio.sleep(1)

    async def _demo_real_time_analysis(self):
        """Demonstra análise em tempo real"""
        print(f"\n⚡ Scenario 3: Real-time Log Analysis")
        print("=" * 40)

        # Simular logs em tempo real
        real_time_logs = [
            "2025-09-15 14:10:00 ERROR Webhook failed: Connection refused",
            "2025-09-15 14:10:05 ERROR Database error: Connection lost",
            "2025-09-15 14:10:10 ERROR AI error: OpenAI API unavailable",
            "2025-09-15 14:10:15 CRITICAL Memory allocation failed",
            "2025-09-15 14:10:20 ERROR HTTP 503 Service Unavailable",
        ]

        print(f"⚡ Simulating real-time log stream...")
        for log_line in real_time_logs:
            self.analytics.add_log_line(log_line, "real-time")
            print(f"📨 New log: {log_line.split(' ', 3)[-1]}")
            await asyncio.sleep(1)

        print(f"✅ Real-time analysis completed")

    async def _demo_insights_generation(self):
        """Demonstra geração de insights"""
        print(f"\n🧠 Scenario 4: Automatic Insights Generation")
        print("=" * 40)

        insights = self.analytics.get_insights()

        print(f"🔍 Generated {len(insights)} insights:")
        for i, insight in enumerate(insights[:5], 1):
            severity_emoji = (
                "🔴"
                if insight.severity >= 8
                else "🟡" if insight.severity >= 6 else "🟢"
            )
            print(
                f"\n{i}. {severity_emoji} {insight.title} (Severity: {insight.severity}/10)"
            )
            print(f"   📝 {insight.description}")
            print(f"   🎯 Confidence: {insight.confidence:.1%}")
            if insight.recommendations:
                print(f"   💡 Recommendation: {insight.recommendations[0]}")

        await asyncio.sleep(2)

    def _show_dashboard(self):
        """Mostra dashboard de logs"""
        print(f"\n📊 DASHBOARD - Log Analytics")
        print("=" * 50)

        dashboard = self.analytics.get_dashboard_data()
        stats = dashboard["stats"]

        print(f"📈 OVERVIEW:")
        print(f"   Total Logs: {stats.get('total', 0):,}")
        print(f"   Error Rate: {stats.get('error_rate_percent', 0):.1f}%")
        print(f"   Recent Errors: {stats.get('recent_errors', 0)}")
        print(f"   Timespan: {stats.get('timespan_hours', 0):.1f} hours")

        print(f"\n📋 LOG LEVELS:")
        for level, count in stats.get("levels", {}).items():
            percentage = (count / stats.get("total", 1)) * 100
            print(f"   {level}: {count} ({percentage:.1f}%)")

        print(f"\n🏷️ PATTERN MATCHES:")
        for pattern, count in sorted(
            dashboard["pattern_matches"].items(), key=lambda x: x[1], reverse=True
        )[:5]:
            print(f"   {pattern}: {count}")

        print(f"\n🚨 RECENT ERRORS:")
        for error in dashboard["recent_errors"]:
            print(f"   {error['datetime']} [{error['level']}] {error['message']}")

        print(f"\n🧠 TOP INSIGHTS:")
        for insight in dashboard["insights"][:3]:
            severity_emoji = (
                "🔴"
                if insight["severity"] >= 8
                else "🟡" if insight["severity"] >= 6 else "🟢"
            )
            print(f"   {severity_emoji} {insight['title']}")

    def _show_final_report(self):
        """Mostra relatório final"""
        print(f"\n📄 FINAL REPORT")
        print("=" * 50)

        report = self.analytics.generate_report()
        print(report)


async def main():
    """Função principal"""
    demo = LogAnalyticsDemo()
    success = await demo.run_log_analytics_demo()
    return success


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
