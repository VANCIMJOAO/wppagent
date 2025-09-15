#!/usr/bin/env python3
"""
TRILHA 2 FASE 3 - Distributed Tracing
Advanced tracing system for end-to-end request tracking
"""

import asyncio
import json
import time
import uuid
from collections import defaultdict
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class SpanKind(Enum):
    """Tipos de span para rastreamento"""

    INTERNAL = "internal"
    SERVER = "server"
    CLIENT = "client"
    PRODUCER = "producer"
    CONSUMER = "consumer"


class SpanStatus(Enum):
    """Status do span"""

    OK = "ok"
    ERROR = "error"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


@dataclass
class TraceSpan:
    """Representa um span individual no trace"""

    span_id: str
    trace_id: str
    parent_span_id: Optional[str]
    operation_name: str
    service_name: str
    kind: SpanKind
    start_time: float
    end_time: Optional[float] = None
    duration_ms: Optional[float] = None
    status: SpanStatus = SpanStatus.OK
    tags: Dict[str, Any] = field(default_factory=dict)
    logs: List[Dict[str, Any]] = field(default_factory=list)

    def finish(self, status: SpanStatus = SpanStatus.OK) -> None:
        """Finaliza o span"""
        self.end_time = time.time()
        self.duration_ms = (self.end_time - self.start_time) * 1000
        self.status = status

    def add_tag(self, key: str, value: Any) -> None:
        """Adiciona tag ao span"""
        self.tags[key] = value

    def add_log(self, message: str, level: str = "info", **kwargs) -> None:
        """Adiciona log ao span"""
        log_entry = {
            "timestamp": time.time(),
            "message": message,
            "level": level,
            **kwargs,
        }
        self.logs.append(log_entry)

    def set_error(self, error: Exception) -> None:
        """Marca span como erro"""
        self.status = SpanStatus.ERROR
        self.add_tag("error", True)
        self.add_tag("error.type", type(error).__name__)
        self.add_tag("error.message", str(error))
        self.add_log(f"Error: {error}", level="error")


class DistributedTracer:
    """Sistema de rastreamento distribuído"""

    def __init__(self, service_name: str = "whatsapp-agent"):
        self.service_name = service_name
        self.spans: Dict[str, TraceSpan] = {}
        self.traces: Dict[str, List[TraceSpan]] = defaultdict(list)
        self.span_processors: List = []
        self.current_context = None

    def add_span_processor(self, processor) -> None:
        """Adiciona processador de span"""
        self.span_processors.append(processor)

    def _generate_span_id(self) -> str:
        """Gera ID único para span"""
        return str(uuid.uuid4())[:16]

    def _generate_trace_id(self) -> str:
        """Gera ID único para trace"""
        return str(uuid.uuid4()).replace("-", "")

    @asynccontextmanager
    async def start_span(
        self,
        operation_name: str,
        kind: SpanKind = SpanKind.INTERNAL,
        parent_span_id: Optional[str] = None,
        tags: Optional[Dict[str, Any]] = None,
    ):
        """Inicia um novo span"""

        # Gerar IDs
        trace_id = (
            self.current_context.get("trace_id")
            if self.current_context
            else self._generate_trace_id()
        )
        span_id = self._generate_span_id()

        # Criar span
        span = TraceSpan(
            span_id=span_id,
            trace_id=trace_id,
            parent_span_id=parent_span_id
            or (self.current_context.get("span_id") if self.current_context else None),
            operation_name=operation_name,
            service_name=self.service_name,
            kind=kind,
            start_time=time.time(),
        )

        # Adicionar tags iniciais
        if tags:
            span.tags.update(tags)

        # Registrar span
        self.spans[span_id] = span
        self.traces[trace_id].append(span)

        # Salvar contexto anterior
        old_context = self.current_context
        self.current_context = {"trace_id": trace_id, "span_id": span_id}

        span.add_log(f"Span started: {operation_name}")

        try:
            yield span
        except Exception as e:
            span.set_error(e)
            raise
        finally:
            # Finalizar span
            span.finish()
            span.add_log(f"Span finished: {operation_name}")

            # Processar span
            for processor in self.span_processors:
                try:
                    processor(span)
                except Exception as e:
                    print(f"Error in span processor: {e}")

            # Restaurar contexto anterior
            self.current_context = old_context

    def create_child_span(
        self,
        operation_name: str,
        kind: SpanKind = SpanKind.INTERNAL,
        tags: Optional[Dict[str, Any]] = None,
    ):
        """Cria span filho do contexto atual"""
        parent_span_id = (
            self.current_context.get("span_id") if self.current_context else None
        )
        return self.start_span(operation_name, kind, parent_span_id, tags)

    def get_trace_summary(self, trace_id: str) -> Dict[str, Any]:
        """Obtém resumo de um trace"""
        spans = self.traces.get(trace_id, [])

        if not spans:
            return {}

        # Calcular métricas
        total_duration = max(span.duration_ms for span in spans if span.duration_ms)
        error_count = sum(1 for span in spans if span.status == SpanStatus.ERROR)

        # Encontrar span raiz
        root_span = next(
            (span for span in spans if span.parent_span_id is None), spans[0]
        )

        return {
            "trace_id": trace_id,
            "root_operation": root_span.operation_name,
            "total_spans": len(spans),
            "total_duration_ms": total_duration,
            "error_count": error_count,
            "start_time": min(span.start_time for span in spans),
            "status": "error" if error_count > 0 else "ok",
        }


class TracingDemo:
    """Demonstração do sistema de tracing"""

    def __init__(self):
        self.tracer = DistributedTracer("whatsapp-agent-demo")
        self.setup_processors()

    def setup_processors(self):
        """Configura processadores de span"""

        def console_processor(span):
            """Processa span para console"""
            print(
                f"📊 Span: {span.operation_name} ({span.duration_ms:.2f}ms) - {span.status.value}"
            )

        self.tracer.add_span_processor(console_processor)

    async def simulate_webhook_processing(self):
        """Simula processamento de webhook com tracing"""

        async with self.tracer.start_span(
            "webhook.receive",
            SpanKind.SERVER,
            tags={"webhook.type": "whatsapp", "webhook.source": "meta"},
        ) as webhook_span:
            webhook_span.add_log("Webhook received from WhatsApp")

            # Simular validação
            async with self.tracer.create_child_span(
                "webhook.validate"
            ) as validate_span:
                validate_span.add_tag("validation.type", "signature")
                await asyncio.sleep(0.01)  # Simular processamento
                validate_span.add_log("Webhook signature validated")

            # Simular processamento de mensagem
            async with self.tracer.create_child_span(
                "message.process",
                SpanKind.INTERNAL,
                {"message.type": "text", "message.from": "+5511999999999"},
            ) as msg_span:
                msg_span.add_log("Starting message processing")

                # Simular extração de dados
                async with self.tracer.create_child_span(
                    "message.extract"
                ) as extract_span:
                    extract_span.add_tag(
                        "extraction.fields", ["text", "from", "timestamp"]
                    )
                    await asyncio.sleep(0.005)
                    extract_span.add_log("Message data extracted")

                # Simular processamento IA
                async with self.tracer.create_child_span(
                    "ai.process",
                    SpanKind.CLIENT,
                    {"ai.provider": "openai", "ai.model": "gpt-4"},
                ) as ai_span:
                    await asyncio.sleep(0.1)  # Simular tempo de IA
                    ai_span.add_tag("ai.tokens_used", 150)
                    ai_span.add_log("AI response generated")

                # Simular envio de resposta
                async with self.tracer.create_child_span(
                    "whatsapp.send",
                    SpanKind.CLIENT,
                    {"whatsapp.to": "+5511999999999", "whatsapp.message_type": "text"},
                ) as send_span:
                    await asyncio.sleep(0.05)
                    send_span.add_tag("whatsapp.message_id", "msg_12345")
                    send_span.add_log("Response sent to WhatsApp")

                msg_span.add_log("Message processing completed")

            webhook_span.add_log("Webhook processing completed successfully")

    async def simulate_error_scenario(self):
        """Simula cenário com erro"""

        async with self.tracer.start_span("error.scenario") as error_span:
            try:
                async with self.tracer.create_child_span("database.query") as db_span:
                    db_span.add_tag("query.type", "SELECT")
                    db_span.add_tag("table", "conversations")

                    # Simular erro de banco
                    await asyncio.sleep(0.02)
                    raise Exception("Database connection timeout")

            except Exception as e:
                error_span.add_log("Database error occurred, implementing fallback")

                # Simular fallback
                async with self.tracer.create_child_span(
                    "cache.fallback"
                ) as cache_span:
                    cache_span.add_tag("cache.type", "redis")
                    await asyncio.sleep(0.01)
                    cache_span.add_log("Fallback data retrieved from cache")

    async def simulate_concurrent_requests(self):
        """Simula requests concorrentes"""

        async def process_request(request_id: str):
            async with self.tracer.start_span(
                f"request.{request_id}",
                tags={"request.id": request_id, "request.type": "concurrent"},
            ) as request_span:
                # Simular processamento variável
                processing_time = 0.02 + (int(request_id) * 0.01)
                await asyncio.sleep(processing_time)

                request_span.add_tag("processing.time_ms", processing_time * 1000)
                request_span.add_log(f"Request {request_id} processed")

        # Executar 5 requests concorrentes
        tasks = [process_request(str(i)) for i in range(5)]
        await asyncio.gather(*tasks)

    async def run_tracing_demo(self):
        """Executa demonstração completa"""
        print("🎯 TRILHA 2 FASE 3 - Distributed Tracing Demo")
        print("📊 Demonstração de Rastreamento Distribuído")
        print("=" * 60)

        scenarios = [
            ("Webhook Processing", self.simulate_webhook_processing),
            ("Error Scenario", self.simulate_error_scenario),
            ("Concurrent Requests", self.simulate_concurrent_requests),
        ]

        for scenario_name, scenario_func in scenarios:
            print(f"\n🔍 Scenario: {scenario_name}")
            print("-" * 40)

            start_time = time.time()
            await scenario_func()
            end_time = time.time()

            print(f"⏱️ Completed in {(end_time - start_time) * 1000:.2f}ms")

        # Estatísticas finais
        print(f"\n📊 Tracing Statistics:")
        print(f"   Total Spans: {len(self.tracer.spans)}")
        print(f"   Total Traces: {len(self.tracer.traces)}")

        # Mostrar traces
        for trace_id, spans in self.tracer.traces.items():
            summary = self.tracer.get_trace_summary(trace_id)
            print(f"\n🔍 Trace: {trace_id[:8]}...")
            print(f"   Operation: {summary['root_operation']}")
            print(f"   Duration: {summary['total_duration_ms']:.2f}ms")
            print(f"   Spans: {summary['total_spans']}")
            print(f"   Status: {summary['status']}")

        print(f"\n🎯 Distributed Tracing Demo Completed!")
        return True


async def main():
    """Função principal de demonstração"""
    demo = TracingDemo()
    success = await demo.run_tracing_demo()
    return success


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
