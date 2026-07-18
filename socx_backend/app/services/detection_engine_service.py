"""
Detection Engine service — evaluates all enabled DetectionRule rows
against a single NormalizedLogEntry and creates an Alert for every rule
that matches.

Scope, deliberately: execute-on-call only, single-entry evaluation.
- No scheduling — this service does nothing until evaluate_entry() is
  called explicitly by something else.
- No stateful/sliding-window rules (e.g. "10 failed logins in 5 minutes")
  — those require aggregating across multiple entries over time, which is
  a distinct, larger piece of work than what DetectionRule currently
  models (single-entry, stateless field conditions).
- No batch/bulk scanning of existing log history — the caller decides
  which entry to evaluate and when.
"""
from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert import Alert, AlertSeverity, AlertSource
from app.models.detection_rule import DetectionRule
from app.models.log import Log, LogSourceType, NormalizedLogEntry
from app.repositories.alert_repository import AlertRepository
from app.repositories.detection_rule_repository import DetectionRuleRepository

# AlertSource has four coarse buckets; LogSourceType has eight specific
# ones. This maps each log source to the alert source category its
# resulting alerts should carry.
_SOURCE_TYPE_TO_ALERT_SOURCE: dict[LogSourceType, AlertSource] = {
    LogSourceType.EVTX: AlertSource.WINDOWS,
    LogSourceType.WINDOWS_SECURITY: AlertSource.WINDOWS,
    LogSourceType.LINUX_AUTH: AlertSource.LINUX,
    LogSourceType.APACHE: AlertSource.WEB_APPLICATION,
    LogSourceType.NGINX: AlertSource.WEB_APPLICATION,
    LogSourceType.APPLICATION: AlertSource.WEB_APPLICATION,
    LogSourceType.JSON: AlertSource.NETWORK,
    LogSourceType.CSV: AlertSource.NETWORK,
}
_DEFAULT_ALERT_SOURCE = AlertSource.NETWORK


class DetectionEngineService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.rules = DetectionRuleRepository(db)
        self.alerts = AlertRepository(db)

    async def evaluate_entry(self, entry: NormalizedLogEntry) -> list[Alert]:
        """
        Evaluates every currently-enabled detection rule against `entry`.
        Creates and persists one Alert per matching rule, committing if
        anything matched. Returns the list of Alerts created — empty if
        nothing matched or no rules are enabled.
        """
        rules = await self.rules.list_enabled()
        if not rules:
            return []

        alert_source = await self._resolve_alert_source(entry.log_id)

        created: list[Alert] = []
        for rule in rules:
            matched_conditions = self._match(rule, entry)
            if matched_conditions is None:
                continue

            alert = await self.alerts.create_from_match(
                rule=rule,
                entry=entry,
                severity=AlertSeverity(rule.severity.value),
                source=alert_source,
                matched_conditions=matched_conditions,
            )
            created.append(alert)

        if created:
            await self.db.commit()
        return created

    async def _resolve_alert_source(self, log_id: uuid.UUID) -> AlertSource:
        stmt = select(Log.source_type).where(Log.id == log_id)
        result = await self.db.execute(stmt)
        source_type = result.scalar_one_or_none()
        return _SOURCE_TYPE_TO_ALERT_SOURCE.get(source_type, _DEFAULT_ALERT_SOURCE)

    @staticmethod
    def _match(rule: DetectionRule, entry: NormalizedLogEntry) -> Optional[dict]:
        """
        A rule matches an entry when every condition *set* on the rule
        (non-null field) matches the entry — conditions are AND-combined.
        A rule with zero conditions set never matches: an all-null rule is
        a misconfiguration, not a "match everything" wildcard, so it's
        guarded against rather than silently alerting on every entry.

        Returns the dict of conditions that matched (used as evidence) on
        a match, or None on no match.
        """
        matched: dict[str, str] = {}

        if rule.event_id is not None:
            if entry.event_id != rule.event_id:
                return None
            matched["event_id"] = rule.event_id

        if rule.username is not None:
            if not entry.username or entry.username.lower() != rule.username.lower():
                return None
            matched["username"] = rule.username

        if rule.source_ip is not None:
            if not entry.source_ip or str(entry.source_ip) != str(rule.source_ip):
                return None
            matched["source_ip"] = str(rule.source_ip)

        if rule.process_name is not None:
            if not entry.process_name or entry.process_name.lower() != rule.process_name.lower():
                return None
            matched["process_name"] = rule.process_name

        if rule.command_contains is not None:
            if not entry.command_line or rule.command_contains.lower() not in entry.command_line.lower():
                return None
            matched["command_contains"] = rule.command_contains

        if not matched:
            return None

        return matched
