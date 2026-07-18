import { createContext, useCallback, useEffect, useState } from 'react'
import { authApi } from '../api/authApi'
import {
  clearTokens,
  getRefreshToken,
  registerSessionExpiredHandler,
  setTokens,
} from '../api/tokenStore'

export const AuthContext = createContext(null)

// 'loading' -> attempting to restore a session from a stored refresh token
// 'authenticated' / 'unauthenticated' -> settled states
export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [status, setStatus] = useState('loading')

  const logout = useCallback(async () => {
    const refreshToken = getRefreshToken()
    if (refreshToken) {
      // Best-effort: revoke server-side, but don't block the local logout
      // on it — the user should be able to log out even if the API call
      // fails (e.g. they're offline).
      authApi.logout(refreshToken).catch(() => {})
    }
    clearTokens()
    setUser(null)
    setStatus('unauthenticated')
  }, [])

  // Wire the Axios client's "refresh failed" signal to a real logout,
  // so an expired/revoked refresh token anywhere in the app drops the
  // user back to the login screen instead of leaving them stuck on a
  // page that silently stops working.
  useEffect(() => {
    registerSessionExpiredHandler(() => {
      clearTokens()
      setUser(null)
      setStatus('unauthenticated')
    })
  }, [])

  // On first load, if a refresh token survived from a previous session
  // (localStorage), try to turn it into a fresh access token + user
  // profile before deciding whether the person is logged in.
  useEffect(() => {
    const refreshToken = getRefreshToken()
    if (!refreshToken) {
      setStatus('unauthenticated')
      return
    }

    authApi
      .refresh(refreshToken)
      .then((tokens) => {
        setTokens(tokens)
        return authApi.me()
      })
      .then((profile) => {
        setUser(profile)
        setStatus('authenticated')
      })
      .catch(() => {
        clearTokens()
        setStatus('unauthenticated')
      })
  }, [])

  const login = useCallback(async (username, password) => {
    const tokens = await authApi.login(username, password)
    setTokens(tokens)
    const profile = await authApi.me()
    setUser(profile)
    setStatus('authenticated')
    return profile
  }, [])

  const value = {
    user,
    status,
    isAuthenticated: status === 'authenticated',
    isLoading: status === 'loading',
    login,
    logout,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
