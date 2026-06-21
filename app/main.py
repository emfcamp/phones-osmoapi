from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from prometheus_fastapi_instrumentator import Instrumentator

from .config import settings
from .routers import bsc, emf, hlr, msc, telnet


app = FastAPI(
    title="EMF GSM API",
    description="A simple API for managing GSM services at EMF Camp.",
    contact={"name": "EMF GSM Team", "url": "https://gsm.emf.camp/", "email": settings.contact_email},
    version="0.1.0",
    terms_of_service="https://gsm.emf.camp/api/tos",
    license_info={"name": "Beerware", "url": "https://spdx.org/licenses/Beerware.html"},
)

Instrumentator().instrument(app).expose(app)

app.include_router(emf.router)
app.include_router(bsc.router)
app.include_router(hlr.router)
app.include_router(msc.router)
app.include_router(telnet.router)


@app.get("/", include_in_schema=False)
async def read_root():
    """Redirect root to the EMF GSM page."""
    return RedirectResponse(url="https://gsm.emf.camp/")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
