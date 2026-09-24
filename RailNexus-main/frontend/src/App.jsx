import { Navigate, Route, Routes } from "react-router-dom";
import AppLayout from "./layouts/AppLayout";
import Analytics from "./pages/Analytics";
import Dashboard from "./pages/Dashboard";
import {
  Alerts, Assets, BlockRequests, Calendar, Conflicts, Execution,
  Maintenance, MonthlyPlanning, Sections, SettingsPage, Trains,
} from "./pages/DataPages";
import Planning from "./pages/Planning";
import { Landing, Login } from "./pages/PublicPages";
import Reports from "./pages/Reports";
import { getStoredUser } from "./services/api";
import WhatIf from "./pages/WhatIf";

function Protected() {
  return localStorage.getItem("railnexus_token")&&getStoredUser() ? <AppLayout/> : <Navigate to="/login" replace/>;
}

export default function App() {
  return <Routes>
    <Route path="/" element={<Landing/>}/>
    <Route path="/login" element={<Login/>}/>
    <Route element={<Protected/>}>
      <Route path="/dashboard" element={<Dashboard/>}/>
      <Route path="/sections" element={<Sections/>}/>
      <Route path="/assets" element={<Assets/>}/>
      <Route path="/trains" element={<Trains/>}/>
      <Route path="/maintenance" element={<Maintenance/>}/>
      <Route path="/block-requests" element={<BlockRequests/>}/>
      <Route path="/block-planning" element={<Planning/>}/>
      <Route path="/calendar" element={<Calendar/>}/>
      <Route path="/monthly-planning" element={<MonthlyPlanning/>}/>
      <Route path="/conflicts" element={<Conflicts/>}/>
      <Route path="/what-if" element={<WhatIf/>}/>
      <Route path="/execution" element={<Execution/>}/>
      <Route path="/analytics" element={<Analytics/>}/>
      <Route path="/reports" element={<Reports/>}/>
      <Route path="/alerts" element={<Alerts/>}/>
      <Route path="/settings" element={<SettingsPage/>}/>
    </Route>
    <Route path="*" element={<Navigate to="/" replace/>}/>
  </Routes>;
}
