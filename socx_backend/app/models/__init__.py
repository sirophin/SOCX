"""
Import all models here so Alembic's autogenerate can discover every table
via `Base.metadata` — a common gotcha if models are imported lazily elsewhere.
"""
from app.db.base import Base  # noqa: F401

from app.models.role import Role, RoleName  # noqa: F401
from app.models.user import User  # noqa: F401
from app.models.log import Log, NormalizedLogEntry, LogSourceType, LogSeverity  # noqa: F401
from app.models.mitre_technique import MitreTechnique  # noqa: F401
from app.models.detection_rule import DetectionRule  # noqa: F401
from app.models.alert import Alert, AlertLogEntry, AlertSeverity, AlertStatus, AlertSource  # noqa: F401
from app.models.incident import Incident, IncidentAlert, IncidentSeverity, IncidentStatus  # noqa: F401
from app.models.investigation_note import InvestigationNote  # noqa: F401
from app.models.ioc import IOC, IOCType  # noqa: F401
from app.models.report import Report  # noqa: F401
from app.models.audit_log import AuditLog  # noqa: F401
from app.models.refresh_token import RefreshToken  # noqa: F401

__all__ = [
    "Base",
    "Role", "RoleName",
    "User",
    "Log", "NormalizedLogEntry", "LogSourceType", "LogSeverity",
    "MitreTechnique",
    "DetectionRule",
    "Alert", "AlertLogEntry", "AlertSeverity", "AlertStatus", "AlertSource",
    "Incident", "IncidentAlert", "IncidentSeverity", "IncidentStatus",
    "InvestigationNote",
    "IOC", "IOCType",
    "Report",
    "AuditLog",
    "RefreshToken",
]
