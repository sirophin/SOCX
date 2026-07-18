// These must match the backend's enum *values* exactly (Pydantic validates
// query params against the enum's value strings, not any normalized form).

// AlertStatus / IncidentStatus values are Title Case in the backend model.
export const ALERT_STATUSES = ['Open', 'Investigating', 'Contained', 'Resolved', 'Closed']

// AlertSeverity / RuleSeverity / LogSeverity values are all lowercase.
export const SEVERITIES = ['low', 'medium', 'high', 'critical']

export const ALERT_SOURCES = ['windows', 'linux', 'web_application', 'network']

// Log parsing lifecycle (Log.parse_status).
export const PARSE_STATUSES = ['pending', 'parsing', 'completed', 'partial', 'failed']

export const ROLES = ['Admin', 'Tier 1 Analyst', 'Tier 2 Analyst']

// Roles permitted to manage detection rules (create/edit/delete) — must
// match the backend's `can_manage_rules` permission grants from the
// roles seed data (Admin and Tier 2 Analyst; Tier 1 Analyst does not).
export const RULE_MANAGER_ROLES = ['Admin', 'Tier 2 Analyst']
