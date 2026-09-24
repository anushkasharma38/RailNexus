import {
  Activity, AlertTriangle, BarChart3, Blocks, CalendarDays, ClipboardCheck,
  Construction, FileText, GitCompareArrows, LayoutDashboard, LogOut, Menu, PackageSearch,
  Settings, TrainFront, Waypoints, X, Zap,
} from "lucide-react";
import { useState } from "react";
import { NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import { api, getStoredUser } from "../services/api";

const links = [
  ["/dashboard", "Overview", LayoutDashboard],
  ["/sections", "Railway Sections", Waypoints],
  ["/assets", "Assets", PackageSearch],
  ["/trains", "Trains & Timetable", TrainFront],
  ["/maintenance", "Maintenance", Construction],
  ["/block-requests", "Block Requests", ClipboardCheck],
  ["/block-planning", "Automatic Planning", Zap],
  ["/calendar", "Block Calendar", CalendarDays],
  ["/monthly-planning", "Monthly Planning", CalendarDays],
  ["/conflicts", "Conflicts", AlertTriangle],
  ["/what-if", "What-If Simulation", GitCompareArrows],
  ["/execution", "Execution", Activity],
  ["/analytics", "Analytics", BarChart3],
  ["/reports", "Reports", FileText],
  ["/alerts", "Alerts", Blocks],
  ["/settings", "Settings", Settings],
];

export default function AppLayout() {
  const [open, setOpen] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();
  const user = getStoredUser() || {};
  const title = links.find(([path]) => location.pathname.startsWith(path))?.[1] || "Operations";
  async function logout() {
    try { await api("/auth/logout/", { method: "POST" }); } catch {}
    localStorage.removeItem("railnexus_token");
    localStorage.removeItem("railnexus_user");
    navigate("/login");
  }
  return <div className="min-h-screen bg-slate-100">
    <aside className={`fixed inset-y-0 left-0 z-40 w-72 bg-rail-950 text-white transition-transform lg:translate-x-0 ${open ? "translate-x-0" : "-translate-x-full"}`}>
      <div className="flex h-20 items-center justify-between border-b border-white/10 px-6">
        <NavLink to="/" className="flex items-center gap-3"><span className="grid h-10 w-10 place-items-center rounded-lg bg-white text-rail-900"><TrainFront/></span><span><b className="brand-serif text-xl">RailNexus</b><small className="block text-[10px] uppercase tracking-widest text-blue-200">Control Platform</small></span></NavLink>
        <button className="lg:hidden" onClick={() => setOpen(false)}><X/></button>
      </div>
      <nav className="scrollbar h-[calc(100vh-160px)] overflow-y-auto px-3 py-4">{links.map(([path, label, Icon]) =>
        <NavLink onClick={() => setOpen(false)} key={path} to={path} className={({isActive}) => `mb-1 flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition ${isActive ? "bg-white text-rail-950 shadow" : "text-slate-300 hover:bg-white/10 hover:text-white"}`}><Icon size={18}/>{label}</NavLink>
      )}</nav>
      <div className="absolute bottom-0 w-full border-t border-white/10 p-4"><button onClick={logout} className="flex w-full items-center gap-3 rounded-lg p-2 text-sm text-slate-300 hover:bg-white/10"><LogOut size={18}/> Sign out</button></div>
    </aside>
    <div className="lg:pl-72">
      <header className="sticky top-0 z-30 flex h-20 items-center justify-between border-b bg-white/95 px-4 backdrop-blur md:px-8">
        <div className="flex items-center gap-3"><button className="lg:hidden" onClick={() => setOpen(true)}><Menu/></button><div><h1 className="text-xl font-bold text-rail-950">{title}</h1><p className="text-xs text-slate-500">Demo Railway Division · Simulated Railway Data</p></div></div>
        <div className="text-right"><p className="text-sm font-semibold">{user.username}</p><p className="text-xs text-slate-500">{String(user.role || "").replaceAll("_", " ")}</p></div>
      </header>
      <main className="mx-auto max-w-[1600px] p-4 md:p-8"><Outlet/></main>
    </div>
  </div>;
}
