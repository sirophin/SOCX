/**
 * Token storage strategy (deliberate, not incidental):
 *   - access_token  -> kept ONLY in memory (a module-level variable here).
 *                      Never touches localStorage/sessionStorage, so it
 *                      isn't readable by anything that can read storage —
 *                      it only exists for the life of the tab.
 *   - refresh_token -> the backend's /auth/login and /auth/refresh return
 *                      it directly in the JSON body (there is no httpOnly
 *                      cookie in this API), so the frontend has no choice
 *                      but to hold it client-side somewhere JS-accessible
 *                      to use it at all. localStorage is used so a page
 *                      reload doesn't force a fresh login every time.
 *
 * This module is the single source of truth for both, so the Axios
 * client (plain JS, outside React) and AuthContext (React) never drift
 * out of sync with each other.
 */

const REFRESH_TOKEN_KEY = 'socx.refresh_token'

let accessToken = null

export function getAccessToken() {
  return accessToken
}

export function setAccessToken(token) {
  accessToken = token
}

export function getRefreshToken() {
  return localStorage.getItem(REFRESH_TOKEN_KEY)
}

export function setRefreshToken(token) {
  if (token) {
    localStorage.setItem(REFRESH_TOKEN_KEY, token)
  } else {
    localStorage.removeItem(REFRESH_TOKEN_KEY)
  }
}

export function setTokens({ access_token, refresh_token }) {
  setAccessToken(access_token)
  setRefreshToken(refresh_token)
}

export function clearTokens() {
  accessToken = null
  setRefreshToken(null)
}

/**
 * Registered by AuthContext so the Axios client can force a logout when a
 * refresh attempt fails (e.g. the refresh token itself expired/was
 * revoked) — without the client module needing to import React.
 */
let onSessionExpired = () => {}

export function registerSessionExpiredHandler(handler) {
  onSessionExpired = handler
}

export function notifySessionExpired() {
  onSessionExpired()
}
