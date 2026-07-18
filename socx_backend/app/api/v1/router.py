"""
Aggregates all v1 API routers under a single APIRouter mounted at /api/v1.
"""
from fastapi import APIRouter

from app.api.v1.endpoints import alerts, auth, detection_rules, investigation, logs, simulator, users

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(logs.router)
api_router.include_router(investigation.router)
api_router.include_router(detection_rules.router)
api_router.include_router(alerts.router)
api_router.include_router(simulator.router)

# Future routers (incidents, iocs, mitre, reports, dashboard) get included
# here as each module is built, per the Suggested Development Order in
# docs/architecture.md Section 16.
