import logging

from fastapi import Depends, FastAPI, status
from fastapi.responses import RedirectResponse, Response
from prometheus_client import CONTENT_TYPE_LATEST, GC_COLLECTOR, PLATFORM_COLLECTOR, REGISTRY, generate_latest
from prometheus_fastapi_instrumentator import Instrumentator, metrics

from .config import settings
from .dependencies import bsc_instance, hlr_instance, msc_instance, verify_metrics_token
from .routers import bsc, emf, hlr, msc, telnet


class EndpointFilter(logging.Filter):
    """Suppress 2xx access logs for noisy healthcheck/metrics endpoints."""

    def __init__(self, paths: tuple[str, ...] = ("/health", "/metrics")):
        super().__init__()
        self.paths = paths

    def filter(self, record: logging.LogRecord) -> bool:
        # uvicorn access log records have args like:
        # (client_addr, method, path, http_version, status_code)
        try:
            args = record.args
            if not args or len(args) < 5:
                return True
            path = args[2]
            status_code = int(args[4])
        except (IndexError, ValueError, TypeError):
            return True

        if path in self.paths and 200 <= status_code < 300:
            return False
        return True


logging.getLogger("uvicorn.access").addFilter(EndpointFilter())


app = FastAPI(
    title="EMF GSM API",
    description="A simple API for managing GSM services at EMF Camp.",
    contact={"name": "EMF GSM Team", "url": "https://gsm.emf.camp/", "email": settings.contact_email},
    version="1.0.0",
    terms_of_service="https://gsm.emf.camp/api/tos",
    license_info={"name": "Beerware", "url": "https://spdx.org/licenses/Beerware.html"},
)


REGISTRY.unregister(GC_COLLECTOR)
REGISTRY.unregister(PLATFORM_COLLECTOR)
Instrumentator().add(
    metrics.default(
        metric_namespace="osmoapi",
    ),
).instrument(app)

app.include_router(emf.router)
app.include_router(bsc.router)
app.include_router(hlr.router)
app.include_router(msc.router)
app.include_router(telnet.router)


@app.get("/", include_in_schema=False)
async def read_root():
    """Redirect root to the EMF GSM page."""
    return RedirectResponse(url="https://gsm.emf.camp/")


@app.get("/metrics", include_in_schema=False, dependencies=[Depends(verify_metrics_token)])
def metrics():
    data = generate_latest(REGISTRY)
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)


@app.get("/osmocom-health", summary="Healtcheck to see if osmocom components are up", tags=["Healthchecks"])
async def healthcheck():
    try:
        return {
            "osmo-bsc": bsc_instance._alive(),
            "osmo-hlr": hlr_instance._alive(),
            "osmo-msc": msc_instance._alive(),
        }
    except Exception:
        return Response(status_code=status.HTTP_503_SERVICE_UNAVAILABLE)


@app.get("/health", summary="Basic API healthcheck", tags=["Healthchecks"])
async def healthcheck():
    return Response(status_code=status.HTTP_204_NO_CONTENT)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
