from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import (
    ConsoleMetricExporter,
    PeriodicExportingMetricReader,
)
from opentelemetry.sdk.resources import Resource

from config import config

_meter_provider: MeterProvider | None = None
_meter: metrics.Meter | None = None

updates_total: metrics.Counter | None = None
rate_limited_total: metrics.Counter | None = None
handler_errors_total: metrics.Counter | None = None
handler_duration_ms: metrics.Histogram | None = None


def setup_metrics() -> None:
    global _meter_provider, _meter
    global updates_total, rate_limited_total, handler_errors_total, handler_duration_ms

    if not config.METRICS_ENABLED or _meter_provider is not None:
        return

    resource = Resource.create({"service.name": config.OTEL_SERVICE_NAME})
    reader = PeriodicExportingMetricReader(
        ConsoleMetricExporter(),
        export_interval_millis=int(config.METRICS_EXPORT_INTERVAL_SEC * 1000),
    )
    provider = MeterProvider(resource=resource, metric_readers=[reader])
    metrics.set_meter_provider(provider)
    _meter_provider = provider

    _meter = metrics.get_meter(__name__)
    updates_total = _meter.create_counter(
        "bot.updates.total",
        description="Telegram updates received",
    )
    rate_limited_total = _meter.create_counter(
        "bot.rate_limited.total",
        description="Updates rejected by rate limiter",
    )
    handler_errors_total = _meter.create_counter(
        "bot.handler.errors.total",
        description="Handler exceptions",
    )
    handler_duration_ms = _meter.create_histogram(
        "bot.handler.duration",
        unit="ms",
        description="Handler execution time",
    )


def shutdown_metrics() -> None:
    global _meter_provider, _meter
    global updates_total, rate_limited_total, handler_errors_total, handler_duration_ms

    if _meter_provider is None:
        return
    _meter_provider.shutdown()
    _meter_provider = None
    _meter = None
    updates_total = None
    rate_limited_total = None
    handler_errors_total = None
    handler_duration_ms = None
