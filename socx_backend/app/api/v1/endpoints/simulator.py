"""
Attack Simulator endpoints — start/stop/status for a background task that
generates realistic synthetic security events every 2 seconds, feeding
them through the real parsing and detection pipeline (same parsers, same
DetectionEngineService, same Alert creation path used for actual
uploaded logs) — see app/services/simulator_service.py for the mechanics.

Open to any authenticated, active analyst. This is a testing/demo
utility, not a privileged action — consistent with how log upload and
alert acknowledgment are already scoped in this app (only detection-rule
and user management get a stricter permission gate). Note that the
simulator is a single, process-wide background task: start/stop affects
the whole running backend, not a per-user simulation.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.v1.deps import get_current_active_user
from app.models.user import User
from app.schemas.simulator import SimulatorActionResponse, SimulatorStatusOut
from app.services.simulator_service import simulator_service

router = APIRouter(prefix="/simulator", tags=["Attack Simulator"])


@router.post("/start", response_model=SimulatorActionResponse)
async def start_simulator(
    current_user: User = Depends(get_current_active_user),
) -> SimulatorActionResponse:
    started = simulator_service.start()
    message = "Simulator started" if started else "Simulator is already running"
    return SimulatorActionResponse(running=simulator_service.is_running, message=message)


@router.post("/stop", response_model=SimulatorActionResponse)
async def stop_simulator(
    current_user: User = Depends(get_current_active_user),
) -> SimulatorActionResponse:
    stopped = await simulator_service.stop()
    message = "Simulator stopped" if stopped else "Simulator was not running"
    return SimulatorActionResponse(running=simulator_service.is_running, message=message)


@router.get("/status", response_model=SimulatorStatusOut)
async def simulator_status(
    current_user: User = Depends(get_current_active_user),
) -> SimulatorStatusOut:
    return SimulatorStatusOut(**simulator_service.status())
