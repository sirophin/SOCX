import Simulation from './pages/Simulation'
import { BrowserRouter, Route, Routes } from 'react-router-dom'
import { AuthProvider } from './auth/AuthContext'
import ProtectedRoute from './auth/ProtectedRoute'
import RoleRoute from './auth/RoleRoute'
import AppShell from './components/layout/AppShell'

import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import UploadLogs from './pages/UploadLogs'
import Investigation from './pages/Investigation'
import DetectionRules from './pages/DetectionRules'
import SampleDatasets from './pages/SampleDatasets'
import Alerts from './pages/Alerts'
import Users from './pages/Users'
import Settings from './pages/Settings'
import NotFound from './pages/NotFound'

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<Login />} />

          <Route element={<ProtectedRoute />}>
            <Route element={<AppShell />}>
              <Route index element={<Dashboard />} handle={{ title: 'Dashboard' }} />
              <Route path="upload" element={<UploadLogs />} handle={{ title: 'Upload Logs' }} />
              <Route
                path="investigation"
                element={<Investigation />}
                handle={{ title: 'Investigation' }}
              />
              <Route path="alerts" element={<Alerts />} handle={{ title: 'Alerts' }} />
              <Route
                path="detection-rules"
                element={<DetectionRules />}
                handle={{ title: 'Detection Rules' }}
              />
              <Route
                path="sample-datasets"
                element={<SampleDatasets />}
                handle={{ title: 'Sample Datasets' }}
              />
<Route
  path="simulation"
  element={<Simulation />}
  handle={{ title: 'Attack Simulator' }}
/>
              <Route element={<RoleRoute allowedRoles={['Admin']} />}>
                <Route path="users" element={<Users />} handle={{ title: 'Users' }} />
              </Route>
              <Route path="settings" element={<Settings />} handle={{ title: 'Settings' }} />
            </Route>
          </Route>

          <Route path="*" element={<NotFound />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  )
}
