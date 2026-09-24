import { ArrowRight, CalendarClock, GitMerge, ShieldCheck, TrainFront, Waypoints, Zap } from "lucide-react";
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../services/api";
import { Button, Card, Field, inputClass } from "../components/ui";

export function Landing() {
  return <div className="min-h-screen bg-white">
    <nav className="mx-auto flex max-w-7xl items-center justify-between px-6 py-5"><Link to="/" className="flex items-center gap-3 text-rail-950"><span className="rounded-lg bg-rail-900 p-2 text-white"><TrainFront/></span><b className="brand-serif text-2xl">RailNexus</b></Link><Link to="/login"><Button>Operations Login</Button></Link></nav>
    <main>
      <section className="relative overflow-hidden bg-rail-950 text-white"><div className="track-grid absolute inset-y-0 right-0 w-2/5 opacity-80"/><div className="relative mx-auto grid max-w-7xl gap-10 px-6 py-24 lg:grid-cols-2 lg:py-32"><div><p className="mb-5 text-sm font-semibold uppercase tracking-[.25em] text-blue-300">SIH26027 · Operations Prototype</p><h1 className="brand-serif text-5xl leading-tight md:text-6xl">AI-Powered Automatic Block Planning</h1><p className="mt-6 max-w-xl text-xl text-slate-300">Maximizing Asset Availability for Train Operations through explainable priority scoring and train-aware scheduling.</p><div className="mt-9 flex gap-3"><Link to="/login"><Button className="bg-white !text-rail-950 hover:bg-blue-50">Open Control Dashboard <ArrowRight className="ml-2 inline" size={17}/></Button></Link></div><p className="mt-5 text-xs text-blue-200">Prototype using clearly simulated railway operational data.</p></div><Corridor/></div></section>
      <section className="mx-auto max-w-7xl px-6 py-20"><div className="mb-10 max-w-2xl"><p className="text-sm font-bold uppercase tracking-wider text-rail-700">Coordinated planning</p><h2 className="brand-serif mt-2 text-4xl text-rail-950">One operational view, from request to execution</h2></div><div className="grid gap-5 md:grid-cols-3">{[
        [Zap, "Explainable prioritization", "Configurable weighted scoring shows why every maintenance task is prioritized."],
        [GitMerge, "Multi-department blocks", "Engineering, Traction and S&T work is coordinated within compatible windows."],
        [CalendarClock, "Dynamic replanning", "Simulate delays, compare outcomes and select the next conflict-free window."],
      ].map(([Icon, title, text]) => <Card key={title}><Icon className="text-rail-700"/><h3 className="mt-4 font-bold text-rail-950">{title}</h3><p className="mt-2 text-sm leading-6 text-slate-600">{text}</p></Card>)}</div></section>
    </main>
  </div>;
}

function Corridor() {
  return <div className="hidden items-center justify-center lg:flex"><div className="w-full rounded-2xl border border-white/15 bg-white/5 p-8 backdrop-blur"><div className="mb-7 flex items-center gap-2 text-blue-200"><Waypoints/><span className="text-sm">Illustrative corridor</span></div><div className="flex items-center"><span className="h-5 w-5 rounded-full border-4 border-white bg-signal-green"/><span className="h-1 flex-1 bg-white/40"/><span className="h-5 w-5 rounded-full border-4 border-white bg-signal-amber"/><span className="h-1 flex-1 bg-white/40"/><span className="h-5 w-5 rounded-full border-4 border-white bg-signal-green"/></div><div className="mt-3 flex justify-between text-xs"><span>Dharampur</span><span>Nandigram</span><span>Raj Nagar</span></div><div className="mt-8 rounded-lg bg-white/10 p-4 text-sm"><ShieldCheck className="mr-2 inline text-emerald-300" size={18}/>Conflict checking available after login</div></div></div>;
}

export function Login() {
  const navigate = useNavigate();
  const [form, setForm] = useState({username:"control", password:"RailNexus@2026"});
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  async function submit(event) {
    event.preventDefault(); setBusy(true); setError("");
    try {
      const user = await api("/auth/login/", {method:"POST", body:JSON.stringify(form)});
      localStorage.setItem("railnexus_token", user.token);
      localStorage.setItem("railnexus_user", JSON.stringify(user));
      navigate("/dashboard");
    } catch (e) { setError(e.message); } finally { setBusy(false); }
  }
  return <div className="grid min-h-screen bg-slate-100 lg:grid-cols-2"><div className="track-grid hidden p-16 text-white lg:flex lg:flex-col lg:justify-between"><Link to="/" className="flex items-center gap-3"><TrainFront/><b className="brand-serif text-2xl">RailNexus</b></Link><div><h1 className="brand-serif max-w-xl text-5xl">Maintenance windows that respect train movement.</h1><p className="mt-5 max-w-lg text-slate-300">A deterministic, explainable SIH prototype for the Demo Railway Division.</p></div><p className="text-xs text-blue-200">No production railway system is connected.</p></div><div className="grid place-items-center p-6"><form onSubmit={submit} className="w-full max-w-md rounded-2xl border bg-white p-8 shadow-panel"><h2 className="text-2xl font-bold text-rail-950">Operations login</h2><p className="mt-2 text-sm text-slate-500">Use a documented demo account.</p><div className="mt-7 space-y-5"><Field label="Username"><input className={inputClass} value={form.username} onChange={e=>setForm({...form,username:e.target.value})}/></Field><Field label="Password"><input type="password" className={inputClass} value={form.password} onChange={e=>setForm({...form,password:e.target.value})}/></Field>{error&&<p className="rounded-lg bg-red-50 p-3 text-sm text-red-700">{error}</p>}<Button className="w-full" disabled={busy}>{busy?"Signing in…":"Sign in"}</Button></div><p className="mt-5 text-xs text-slate-500">Demo: control / RailNexus@2026</p></form></div></div>;
}
