"""
SOCX API entrypoint.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings

# Importing app.parsers triggers every concrete parser's
# @ParserRegistry.register decorator, populating the registry the Log
# Parser module depends on. Imported here (once, at startup) rather than
# lazily inside the service, so registration failures surface immediately.
import app.parsers  # noqa: F401

app = FastAPI(
    title="SOCX - SOC Monitoring & Incident Response Platform",
    version="0.1.0",
    description="API for the SOCX SOC investigation platform.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/health", tags=["Health"])
async def health_check() -> dict:
    return {"status": "ok"}
