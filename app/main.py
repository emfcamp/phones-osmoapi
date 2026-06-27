from fastapi import FastAPI, Depends
from fastapi.responses import RedirectResponse, Response
from prometheus_fastapi_instrumentator import Instrumentator, metrics
from prometheus_client import REGISTRY, GC_COLLECTOR, PLATFORM_COLLECTOR, generate_latest, CONTENT_TYPE_LATEST

from .config import settings
from .dependencies import verify_metrics_token
from .routers import bsc, emf, hlr, msc, telnet


app = FastAPI(
    title="EMF GSM API",
    description="A simple API for managing GSM services at EMF Camp.",
    contact={"name": "EMF GSM Team", "url": "https://gsm.emf.camp/", "email": settings.contact_email},
    version="0.1.0",
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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
