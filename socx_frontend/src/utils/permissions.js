/**
 * Central role -> permissions mapping. Every role-gated UI decision
 * (sidebar visibility, buttons, actions) should go through the helpers
 * below instead of comparing user.role against a role name inline —
 * keeps RBAC logic in one place instead of scattered role checks.
 *
 * These are a UX convenience only, not a security boundary — the
 * backend enforces the real permission checks regardless of what the
 * frontend shows or hides.
 */

export const PAGES = {
  DASHBOARD: 'dashboard',
  UPLOAD_LOGS: 'upload-logs',
  INVESTIGATION: 'investigation',
  ALERTS: 'alerts',
  DETECTION_RULES: 'detection-rules',
  SAMPLE_DATASETS: 'sample-datasets',
SIMULATION: 'simulation',
  USERS: 'users',
  SETTINGS: 'settings',
}

const ROLE_PERMISSIONS = {
  Admin: {
    pages: Object.values(PAGES),
    canManageRules: true,
    canManageUsers: true,
    canDelete: true,
  },
  'Tier 2 Analyst': {
    pages: [
      PAGES.DASHBOARD,
      PAGES.UPLOAD_LOGS,
      PAGES.INVESTIGATION,
      PAGES.ALERTS,
      PAGES.DETECTION_RULES,
      PAGES.SAMPLE_DATASETS,
PAGES.SIMULATION,
      PAGES.SETTINGS,
    ],
    canManageRules: true,
    canManageUsers: false,
    canDelete: false,
  },
  'Tier 1 Analyst': {
    pages: [
      PAGES.DASHBOARD,
      PAGES.UPLOAD_LOGS,
      PAGES.INVESTIGATION,
      PAGES.ALERTS,
      PAGES.SAMPLE_DATASETS,
PAGES.SIMULATION,
    ],
    canManageRules: false,
    canManageUsers: false,
    canDelete: false,
  },
}

const DEFAULT_PERMISSIONS = {
  pages: [],
  canManageRules: false,
  canManageUsers: false,
  canDelete: false,
}

export function getPermissions(role) {
  return ROLE_PERMISSIONS[role] || DEFAULT_PERMISSIONS
}

export function canViewPage(role, page) {
  return getPermissions(role).pages.includes(page)
}

export function canManageRules(role) {
  return getPermissions(role).canManageRules
}

export function canManageUsers(role) {
  return getPermissions(role).canManageUsers
}

export function canDelete(role) {
  return getPermissions(role).canDelete
}
