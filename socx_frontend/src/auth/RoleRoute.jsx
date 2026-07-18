import { Navigate, Outlet } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'

/**
 * Gates a route to specific roles, on top of ProtectedRoute's auth check.
 * Role strings must match the backend's RoleName values exactly:
 * "Admin", "Tier 1 Analyst", "Tier 2 Analyst".
 */
export default function RoleRoute({ allowedRoles }) {
  const { user } = useAuth()

  if (!user || !allowedRoles.includes(user.role)) {
    return <Navigate to="/" replace />
  }

  return <Outlet />
}
