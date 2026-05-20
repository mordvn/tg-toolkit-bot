from contextlib import contextmanager
from typing import Iterator

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

from config import config

_tracer_provider: TracerProvider | None = None


def setup_tracing() -> None:
    global _tracer_provider
    if not config.TRACE_ENABLED or _tracer_provider is not None:
        return

    resource = Resource.create({"service.name": config.OTEL_SERVICE_NAME})
    provider = TracerProvider(resource=resource)
    provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
    trace.set_tracer_provider(provider)
    _tracer_provider = provider


def shutdown_tracing() -> None:
    global _tracer_provider
    if _tracer_provider is None:
        return
    _tracer_provider.shutdown()
    _tracer_provider = None


def get_tracer(name: str) -> trace.Tracer:
    return trace.get_tracer(name)


@contextmanager
def span(name: str, **attributes: str | int | bool) -> Iterator[trace.Span]:
    tracer = get_tracer(__name__)
    with tracer.start_as_current_span(name) as current:
        for key, value in attributes.items():
            current.set_attribute(key, value)
        yield current
