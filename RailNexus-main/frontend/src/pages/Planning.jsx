import { Check, RefreshCw, ShieldAlert, Sparkles, X } from "lucide-react";
import { useEffect, useState } from "react";
import { api, formatDateTime, list } from "../services/api";
import { Badge, Button, Card, ErrorState, LoadingState, Table } from "../components/ui";

export default function Planning() {
  const [plans,setPlans]=useState(null),[tasks,setTasks]=useState([]),[selected,setSelected]=useState([]),[busy,setBusy]=useState(false),[message,setMessage]=useState(""),[error,setError]=useState("");
  const role=JSON.parse(localStorage.getItem("railnexus_user")||"{}").role;
  const canControl=["ADMIN","CONTROL_OFFICE"].includes(role);
  const load=()=>{setError("");return Promise.all([list("block-plans"),list("tasks")]).then(([p,t])=>{setPlans(p);setTasks(t)}).catch(e=>setError(e.message))};
  useEffect(()=>{load()},[]);
  async function run(){setBusy(true);setError("");try{const created=await api("/planning/run/",{method:"POST",body:JSON.stringify({task_ids:selected.length?selected:undefined})});setMessage(`${created.length} optimized block plan(s) generated.`);setSelected([]);load()}catch(e){setError(e.message)}finally{setBusy(false)}}
  async function review(id,decision){setError("");try{const plan=plans.find(p=>p.id===id);const payload={decision};if(decision==="modify"){payload.changes={start_time:new Date(new Date(plan.start_time).getTime()+30*60000).toISOString(),end_time:new Date(new Date(plan.end_time).getTime()+30*60000).toISOString(),reason:`${plan.reason} Control Office shifted this plan by 30 minutes.`}}await api(`/block-plans/${id}/review/`,{method:"POST",body:JSON.stringify(payload)});setMessage(`Plan #${id} ${decision==="modify"?"shifted by 30 minutes":decision+"d"}.`);load()}catch(e){setError(e.data?.conflicts?.map(c=>c.description).join(" ")||e.message)}}
  async function replan(id){setBusy(true);try{const result=await api("/planning/replan/",{method:"POST",body:JSON.stringify({plan_id:id,train_delay:30})});setMessage(`Plan #${id}: ${formatDateTime(result.before.start)} → ${formatDateTime(result.after.start)}. ${result.reason}`);load()}catch(e){setError(e.message)}finally{setBusy(false)}}
  if(!plans&&!error)return <LoadingState/>;
  return <div className="space-y-6">
    {error&&<ErrorState message={error} retry={load}/>}
    {message&&<div className="rounded-lg border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-800">{message}</div>}
    <Card title="Automatic Block Planner" action={canControl&&<Button disabled={busy} onClick={run}><Sparkles className="mr-2 inline" size={16}/>{busy?"Optimizing…":"Run Automatic Planner"}</Button>}><p className="mb-4 text-sm text-slate-600">{canControl?"Select pending tasks or leave all unselected to optimize every eligible task.":"Planning is read-only for department users. Control Office or Admin approval is required for planning actions."} The deterministic engine ranks priorities, groups compatible departments and searches 30-minute train-free windows.</p>{canControl&&<div className="grid gap-2 md:grid-cols-2 xl:grid-cols-3">{tasks.filter(t=>["PENDING","REQUESTED"].includes(t.status)).map(t=><label key={t.id} className={`flex cursor-pointer items-start gap-3 rounded-lg border p-3 ${selected.includes(t.id)?"border-rail-700 bg-blue-50":"border-slate-200"}`}><input type="checkbox" className="mt-1" checked={selected.includes(t.id)} onChange={()=>setSelected(selected.includes(t.id)?selected.filter(id=>id!==t.id):[...selected,t.id])}/><span><b className="text-sm">{t.task_id}</b> <Badge>{t.priority.level}</Badge><small className="mt-1 block text-slate-500">{t.title} · {t.department.replaceAll("_"," ")}</small></span></label>)}</div>}</Card>
    <Card title="Generated Plans"><Table rows={plans||[]} columns={[
      {key:"id",label:"Plan",render:v=>`#${v}`},
      {key:"start_time",label:"Window",render:(v,r)=><><b>{formatDateTime(v)}</b><br/><span className="text-xs text-slate-500">to {formatDateTime(r.end_time)}</span></>},
      {key:"section_name",label:"Section"},{key:"priority_score",label:"Priority",render:v=>`${v}/100`},
      {key:"departments",label:"Coordination",render:(v,r)=><><p>{v.join(" + ")||"Unassigned"}</p><p className="max-w-xs text-xs text-slate-500">{r.reason}</p></>},
      {key:"status",label:"Status",render:v=><Badge>{v}</Badge>},
      {key:"conflicts_detail",label:"Conflicts",render:v=>v.length?<span className="text-red-700"><ShieldAlert className="mr-1 inline" size={16}/>{v.length} displayed</span>:<span className="text-emerald-700">None</span>},
      {key:"actions",label:"Control Office",render:(_,row)=>canControl?<div className="flex flex-wrap gap-1">{["GENERATED","PENDING_APPROVAL","MODIFIED"].includes(row.status)&&<><Button className="!px-2" onClick={()=>review(row.id,"approve")}><Check size={15}/></Button><Button variant="secondary" className="!px-2" onClick={()=>review(row.id,"modify")}>Modify</Button><Button variant="danger" className="!px-2" onClick={()=>review(row.id,"reject")}><X size={15}/></Button></>}<Button variant="secondary" className="!px-2" disabled={busy} onClick={()=>replan(row.id)}><RefreshCw size={15}/></Button></div>:<span className="text-xs text-slate-500">Read only</span>},
    ]}/></Card>
  </div>;
}
