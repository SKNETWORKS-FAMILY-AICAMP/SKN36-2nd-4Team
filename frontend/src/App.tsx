import { Navigate, Route, Routes } from 'react-router-dom'
import { AppShell } from './app/layout/AppShell'
import { DashboardPage } from './features/dashboard/DashboardPage'
import { DataOverviewPage } from './features/data/DataOverviewPage'
import { ModelOverviewPage } from './features/model/ModelOverviewPage'
import { RiskUsersPage } from './features/risk-users/RiskUsersPage'
import { UserDetailPage } from './features/users/UserDetailPage'
import { SurvivalAnalysisPage } from './features/survival/SurvivalAnalysisPage'
import './App.css'

function App() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/risk-users" element={<RiskUsersPage />} />
        <Route path="/users" element={<Navigate to="/risk-users" replace />} />
        <Route path="/users/:playerId" element={<UserDetailPage />} />
        <Route path="/model" element={<ModelOverviewPage />} />
        <Route path="/data" element={<DataOverviewPage />} />
        <Route path="/survival" element={<SurvivalAnalysisPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default App
