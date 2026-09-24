import { AlertTriangle, Blocks, Construction, Gauge } from "lucide-react";
import { useEffect, useState } from "react";
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api, formatDateTime } from "../services/api";
import { Badge, Card, ErrorState, LoadingState, StatCard, Table } from "../components/ui";

export default function Dashboard() {
  const [data, setData] = useState(null), [error, setError] = useState("");
  const load = () => { setError(""); return api("/dashboard/").then(setData).catch(e=>setError(e.message)); };
  useEffect(()=>{load()}, []);
  if (error) return <ErrorState message={error} retry={load}/>;
  if (!data) return <LoadingState/>;
  const trend = data.plans.map((p,i)=>({name:`B${i+1}`, utilization:Number(p.utilization)}));
  return <div className="space-y-6">
    <p className="rounded-lg border border-blue-200 bg-blue-50 p-3 text-sm text-blue-800">{data.source_label} · Dashboard scope: {data.role_scope.replaceAll("_"," ")}</p>
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
      <StatCard label="Active Blocks" value={data.stats.active_blocks} icon={Blocks}/>
      <StatCard label="Pending Tasks" value={data.stats.pending_tasks} icon={Construction}/>
      <StatCard label="Open Conflicts" value={data.stats.conflicts} icon={AlertTriangle}/>
      <StatCard label="Asset Availability" value={data.stats.asset_availability} suffix="%" icon={Gauge}/>
      {["SYSTEM_WIDE"].includes(data.role_scope)&&<StatCard label="Approval Queue" value={data.stats.approval_queue} icon={Blocks}/>}
    </div>
    <div className="grid gap-6 xl:grid-cols-3">
      <Card title="Relevant Block Plans" className="xl:col-span-2"><Table rows={data.plans} columns={[
        {key:"start_time",label:"Window",render:(v,r)=><><p className="font-medium">{formatDateTime(v)}</p><p className="text-xs text-slate-500">to {formatDateTime(r.end_time)}</p></>},
        {key:"section_name",label:"Section"}, {key:"departments",label:"Departments",render:v=>v.join(", ")},
        {key:"status",label:"Status",render:v=><Badge>{v}</Badge>},
      ]}/></Card>
      <Card title="Recent Alerts"><div className="space-y-3">{data.alerts.map(a=><div className="rounded-lg border border-slate-100 p-3" key={a.id}><div className="flex justify-between gap-2"><p className="text-sm font-semibold">{a.title}</p><Badge>{a.severity}</Badge></div><p className="mt-1 text-xs leading-5 text-slate-500">{a.message}</p></div>)}</div></Card>
    </div>
    <div className="grid gap-6 xl:grid-cols-2">
      <Card title="Block Utilization"><div className="h-64">{trend.length?<ResponsiveContainer width="100%" height="100%"><AreaChart data={trend}><defs><linearGradient id="util" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#185080" stopOpacity={.4}/><stop offset="95%" stopColor="#185080" stopOpacity={0}/></linearGradient></defs><CartesianGrid strokeDasharray="3 3" vertical={false}/><XAxis dataKey="name"/><YAxis domain={[0,100]}/><Tooltip/><Area type="monotone" dataKey="utilization" stroke="#185080" fill="url(#util)"/></AreaChart></ResponsiveContainer>:<p className="text-sm text-slate-500">Run the planner to generate utilization data.</p>}</div></Card>
      <Card title="Critical Maintenance"><Table rows={data.critical_tasks} columns={[
        {key:"task_id",label:"Task"}, {key:"title",label:"Activity"}, {key:"priority",label:"Priority",render:v=><div><Badge>{v.level}</Badge><p className="mt-1 text-xs">{v.score}/100</p></div>},
      ]}/></Card>
    </div>
    <Card title="Section Bottlenecks · Next 7 Days"><Table rows={data.bottlenecks} columns={[
      {key:"section",label:"Section"},{key:"date",label:"Date"},{key:"severity",label:"Severity",render:v=><Badge>{v}</Badge>},
      {key:"maintenance_demand",label:"Maintenance Demand"},{key:"train_traffic",label:"Train Traffic"},{key:"available_windows",label:"Available Windows"},
      {key:"reason",label:"Reason",render:v=>v.join(" · ")},
    ]}/></Card>
  </div>;
}
