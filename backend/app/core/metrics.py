from prometheus_client import Counter, Histogram, Gauge, generate_latest
from fastapi import Request
from starlette.responses import Response
import time

# --- 定義 Metrics ---

# API 請求計數（按端點、方法、狀態碼分）
http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)

# API 請求延時（毫秒）
http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    buckets=(0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

# 資料庫連線數
db_connections = Gauge("db_connections", "Current database connections")

# Celery 任務計數
celery_tasks_total = Counter(
    "celery_tasks_total",
    "Total Celery tasks",
    ["task_name", "status"],
)

# --- Middleware：自動記錄 HTTP Metrics ---
async def metrics_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time

    http_requests_total.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code,
    ).inc()

    http_request_duration_seconds.labels(
        method=request.method,
        endpoint=request.url.path,
    ).observe(duration)

    return response

# --- Metrics 端點處理函數 ---
async def metrics_endpoint(request):
    """暴露 /metrics 端點供 Prometheus 抓取"""
    return Response(
        content=generate_latest(),
        media_type="text/plain; charset=utf-8",
    )
