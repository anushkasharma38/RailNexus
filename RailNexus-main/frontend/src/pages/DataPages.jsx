import { useEffect, useMemo, useState } from "react";
import { api, formatDateTime, getStoredUser, list } from "../services/api";
import { Badge, Button, Card, EmptyState, ErrorState, Field, inputClass, LoadingState, Modal, Table } from "../components/ui";

const currentRole = () => getStoredUser()?.role;
const canControl = () => ["ADMIN", "CONTROL_OFFICE"].includes(currentRole());

function useResource(name) {
  const [rows, setRows] = useState(null), [error, setError] = useState("");
  const load = () => { setError(""); return list(name).then(setRows).catch(e=>setError(e.message)); };
  useEffect(()=>{load()}, [name]);
  return {rows,error,load};
}

export function Sections() {
  const {rows,error,load}=useResource("sections");
  if(error)return <ErrorState message={error} retry={load}/>; if(!rows)return <LoadingState/>;
  return <div className="space-y-6"><Card title="Demo Railway Corridor"><div className="overflow-x-auto py-8"><div className="flex min-w-[760px] items-center">{rows.map((s,i)=><div className="contents" key={s.id}>{i===0&&<Station name={s.start_station}/>}<div className="relative h-2 flex-1 bg-rail-800"><span className={`absolute left-1/2 top-1/2 h-4 w-4 -translate-x-1/2 -translate-y-1/2 rounded-full ring-4 ring-white ${s.status==="AVAILABLE"?"bg-signal-green":"bg-signal-amber"}`}/><p className="absolute left-1/2 top-5 w-40 -translate-x-1/2 text-center text-xs font-semibold">{s.code}<br/><span className="font-normal text-slate-500">{s.length} km · {s.asset_count} assets</span></p></div><Station name={s.end_station}/></div>)}</div></div></Card><Card title="Section Register"><Table rows={rows} columns={[{key:"code",label:"Code"},{key:"name",label:"Corridor"},{key:"start_station",label:"From"},{key:"end_station",label:"To"},{key:"length",label:"Length",render:v=>`${v} km`},{key:"status",label:"Status",render:v=><Badge>{v}</Badge>}]}/></Card></div>;
}
const Station=({name})=><div className="relative z-10 grid h-16 w-16 shrink-0 place-items-center rounded-full border-4 border-rail-800 bg-white text-center text-[10px] font-bold shadow">{name}</div>;

export function Assets() {
  const {rows,error,load}=useResource("assets"); if(error)return <ErrorState message={error} retry={load}/>; if(!rows)return <LoadingState/>;
  return <Card title="Asset Availability Register"><Table rows={rows} columns={[{key:"name",label:"Asset"},{key:"asset_type",label:"Type"},{key:"section_name",label:"Section"},{key:"criticality",label:"Criticality",render:v=>`${v}/5`},{key:"health_status",label:"Health",render:v=><Badge>{v}</Badge>},{key:"next_maintenance",label:"Next maintenance"}]}/></Card>;
}

export function Trains() {
  const trains=useResource("trains"), schedules=useResource("schedules"),forecasts=useResource("goods-forecasts");
  if(trains.error||schedules.error||forecasts.error)return <ErrorState message={trains.error||schedules.error||forecasts.error}/>; if(!trains.rows||!schedules.rows||!forecasts.rows)return <LoadingState/>;
  return <div className="grid gap-6 xl:grid-cols-3"><Card title="Simulated Train Register"><Table rows={trains.rows} columns={[{key:"train_number",label:"Number"},{key:"name",label:"Train"},{key:"train_type",label:"Type"},{key:"priority",label:"Priority"}]}/></Card><Card title="Train Timetable" className="xl:col-span-2"><Table rows={schedules.rows} columns={[{key:"train_number",label:"Train"},{key:"section_name",label:"Section"},{key:"arrival_time",label:"Section entry",render:formatDateTime},{key:"departure_time",label:"Section clear",render:formatDateTime}]}/></Card><Card title="Goods Train Forecast · Simulated Railway Data" className="xl:col-span-3"><Table rows={forecasts.rows} columns={[{key:"date",label:"Date"},{key:"section_name",label:"Section"},{key:"expected_train_count",label:"Expected Goods Trains"},{key:"forecast_level",label:"Forecast",render:v=><Badge>{v}</Badge>}]}/></Card></div>;
}

export function Maintenance() {
  const resource=useResource("tasks"), sections=useResource("sections"), assets=useResource("assets");
  const [open,setOpen]=useState(false), [error,setError]=useState("");
  const role=currentRole(), departmentRole=["ENGINEERING","TRACTION","S_AND_T"].includes(role);
  const [form,setForm]=useState({task_id:"",title:"",department:departmentRole?role:"ENGINEERING",section:"",asset:"",criticality:3,urgency:3,safety_risk:3,asset_impact:3,estimated_duration:60,preferred_date:new Date().toISOString().slice(0,10)});
  async function create(e){e.preventDefault();setError("");try{await api("/tasks/",{method:"POST",body:JSON.stringify(form)});setOpen(false);resource.load()}catch(err){setError(err.message)}}
  if(resource.error)return <ErrorState message={resource.error} retry={resource.load}/>; if(!resource.rows||!sections.rows||!assets.rows)return <LoadingState/>;
  return <><Card title="Maintenance Task Register" action={<Button onClick={()=>setOpen(true)}>Create Task</Button>}><Table rows={resource.rows} columns={[{key:"task_id",label:"ID"},{key:"title",label:"Activity"},{key:"department",label:"Department",render:v=>v.replaceAll("_"," ")},{key:"section_name",label:"Section"},{key:"estimated_duration",label:"Duration",render:v=>`${v} min`},{key:"priority",label:"AI Priority",render:v=><div><Badge>{v.level}</Badge><p className="mt-1 text-xs font-semibold">{v.score}/100</p><p className="max-w-xs text-[11px] text-slate-500">{v.reasons.join(" · ")}</p></div>},{key:"status",label:"Status",render:v=><Badge>{v}</Badge>}]}/></Card><Modal title="Create maintenance task" open={open} onClose={()=>setOpen(false)}><form onSubmit={create} className="grid gap-4 sm:grid-cols-2"><Field label="Task ID"><input required className={inputClass} value={form.task_id} onChange={e=>setForm({...form,task_id:e.target.value})}/></Field><Field label="Department"><select disabled={departmentRole} className={inputClass} value={form.department} onChange={e=>setForm({...form,department:e.target.value})}><option value="ENGINEERING">Engineering</option><option value="TRACTION">Traction</option><option value="S_AND_T">S&T</option></select></Field><Field label="Title"><input required className={inputClass} value={form.title} onChange={e=>setForm({...form,title:e.target.value})}/></Field><Field label="Section"><select required className={inputClass} value={form.section} onChange={e=>setForm({...form,section:e.target.value,asset:""})}><option value="">Select…</option>{sections.rows.map(s=><option value={s.id} key={s.id}>{s.name}</option>)}</select></Field><Field label="Asset"><select required className={inputClass} value={form.asset} onChange={e=>setForm({...form,asset:e.target.value})}><option value="">Select…</option>{assets.rows.filter(a=>String(a.section)===String(form.section)).map(a=><option value={a.id} key={a.id}>{a.name}</option>)}</select></Field><Field label="Preferred date"><input type="date" required className={inputClass} value={form.preferred_date} onChange={e=>setForm({...form,preferred_date:e.target.value})}/></Field>{["criticality","urgency","safety_risk","asset_impact"].map(k=><Field key={k} label={k.replace("_"," ")}><input type="number" min="1" max="5" required className={inputClass} value={form[k]} onChange={e=>setForm({...form,[k]:Number(e.target.value)})}/></Field>)}<Field label="Duration (minutes)"><input type="number" min="15" required className={inputClass} value={form.estimated_duration} onChange={e=>setForm({...form,estimated_duration:Number(e.target.value)})}/></Field>{error&&<p className="sm:col-span-2 text-sm text-red-700">{error}</p>}<Button className="sm:col-span-2">Save maintenance task</Button></form></Modal></>;
}

export function BlockRequests() {
  const requests=useResource("block-requests"),tasks=useResource("tasks"); const [open,setOpen]=useState(false),[error,setError]=useState("");
  const role=currentRole(), visibleTasks=["ENGINEERING","TRACTION","S_AND_T"].includes(role)?tasks.rows?.filter(t=>t.department===role):tasks.rows;
  const [form,setForm]=useState({maintenance_task:"",requested_start:"",requested_end:"",remarks:""});
  async function create(e){e.preventDefault();try{await api("/block-requests/",{method:"POST",body:JSON.stringify(form)});setOpen(false);requests.load()}catch(err){setError(err.message)}}
  if(requests.error||tasks.error)return <ErrorState message={requests.error||tasks.error}/>;if(!requests.rows||!tasks.rows)return <LoadingState/>;
  return <><Card title="Maintenance Block Requests" action={<Button onClick={()=>setOpen(true)}>Request Block</Button>}><Table rows={requests.rows} columns={[{key:"task_title",label:"Task"},{key:"requested_start",label:"Requested start",render:formatDateTime},{key:"requested_end",label:"Requested end",render:formatDateTime},{key:"status",label:"Status",render:v=><Badge>{v}</Badge>},{key:"remarks",label:"Remarks"}]}/></Card><Modal open={open} onClose={()=>setOpen(false)} title="Create block request"><form onSubmit={create} className="space-y-4"><Field label="Maintenance task"><select required className={inputClass} value={form.maintenance_task} onChange={e=>setForm({...form,maintenance_task:e.target.value})}><option value="">Select…</option>{visibleTasks.filter(t=>t.status!=="COMPLETED").map(t=><option key={t.id} value={t.id}>{t.task_id} — {t.title}</option>)}</select></Field><Field label="Requested start"><input type="datetime-local" required className={inputClass} onChange={e=>setForm({...form,requested_start:new Date(e.target.value).toISOString()})}/></Field><Field label="Requested end"><input type="datetime-local" required className={inputClass} onChange={e=>setForm({...form,requested_end:new Date(e.target.value).toISOString()})}/></Field><Field label="Remarks"><textarea className={inputClass} value={form.remarks} onChange={e=>setForm({...form,remarks:e.target.value})}/></Field>{error&&<p className="text-sm text-red-700">{error}</p>}<Button>Submit request</Button></form></Modal></>;
}

const addDays=(date,amount)=>new Date(date.getFullYear(),date.getMonth(),date.getDate()+amount);
const startOfWeek=date=>addDays(date,-((date.getDay()+6)%7));
const dateKey=date=>`${date.getFullYear()}-${String(date.getMonth()+1).padStart(2,"0")}-${String(date.getDate()).padStart(2,"0")}`;
const sameDate=(value,date)=>dateKey(new Date(value))===dateKey(date);

function useCalendarRange(start,end) {
  const [plans,setPlans]=useState(null),[error,setError]=useState("");
  const startKey=dateKey(start),endKey=dateKey(end);
  const load=()=>{setError("");setPlans(null);return api(`/calendar/?start=${startKey}&end=${endKey}`).then(data=>setPlans(data.plans)).catch(e=>setError(e.message))};
  useEffect(()=>{load()},[startKey,endKey]);
  return {plans,error,load};
}

function PlanChip({plan,onClick}) {
  return <button onClick={()=>onClick(plan)} className="mb-2 w-full rounded-lg border-l-4 border-rail-700 bg-slate-50 p-2 text-left text-xs hover:bg-blue-50"><b>{new Date(plan.start_time).toLocaleTimeString("en-IN",{hour:"2-digit",minute:"2-digit"})}</b><span className="mt-1 block">{plan.section_name}</span><span className="mt-1 block text-slate-500">{plan.departments.join(" + ")||"No department"}</span><Badge>{plan.status}</Badge></button>;
}

function PlanDetails({plan,onClose}) {
  return <Modal title={plan?`Block Plan #${plan.id}`:"Block Plan"} open={Boolean(plan)} onClose={onClose}>{plan&&<div className="space-y-4 text-sm"><div><p className="text-slate-500">Window</p><p className="font-semibold">{formatDateTime(plan.start_time)} — {formatDateTime(plan.end_time)}</p></div><div><p className="text-slate-500">Section</p><p className="font-semibold">{plan.section_name}</p></div><div><p className="text-slate-500">Departments</p><p>{plan.departments.join(", ")||"—"}</p></div><div><p className="text-slate-500">Status</p><Badge>{plan.status}</Badge></div><div><p className="text-slate-500">Planning explanation</p><p>{plan.reason}</p></div></div>}</Modal>;
}

export function Calendar() {
  const [anchor,setAnchor]=useState(new Date()),[selected,setSelected]=useState(null);
  const weekStart=useMemo(()=>startOfWeek(anchor),[anchor]),weekEnd=useMemo(()=>addDays(weekStart,6),[weekStart]);
  const days=useMemo(()=>Array.from({length:7},(_,index)=>addDays(weekStart,index)),[weekStart]);
  const {plans,error,load}=useCalendarRange(weekStart,weekEnd);
  const controls=<div className="flex flex-wrap gap-2"><Button variant="secondary" onClick={()=>setAnchor(addDays(weekStart,-7))}>Previous week</Button><Button variant="secondary" onClick={()=>setAnchor(new Date())}>Current week</Button><Button variant="secondary" onClick={()=>setAnchor(addDays(weekStart,7))}>Next week</Button></div>;
  if(error)return <ErrorState message={error} retry={load}/>;
  return <><Card title={`${weekStart.toLocaleDateString("en-IN",{day:"numeric",month:"short"})} – ${weekEnd.toLocaleDateString("en-IN",{day:"numeric",month:"short",year:"numeric"})}`} action={controls}>{!plans?<LoadingState/>:<div className="overflow-x-auto"><div className="grid min-w-[900px] grid-cols-7 gap-3">{days.map(day=><div key={dateKey(day)}><h3 className="mb-3 border-b pb-2 text-sm font-bold">{day.toLocaleDateString("en-IN",{weekday:"short",day:"numeric",month:"short"})}</h3>{plans.filter(plan=>sameDate(plan.start_time,day)).map(plan=><PlanChip key={plan.id} plan={plan} onClick={setSelected}/>)}</div>)}</div></div>}</Card><PlanDetails plan={selected} onClose={()=>setSelected(null)}/></>;
}

export function MonthlyPlanning() {
  const [month,setMonth]=useState(()=>new Date(new Date().getFullYear(),new Date().getMonth(),1)),[selected,setSelected]=useState(null);
  const first=useMemo(()=>new Date(month.getFullYear(),month.getMonth(),1),[month]);
  const last=useMemo(()=>new Date(month.getFullYear(),month.getMonth()+1,0),[month]);
  const gridStart=useMemo(()=>startOfWeek(first),[first]);
  const gridEnd=useMemo(()=>addDays(startOfWeek(last),6),[last]);
  const days=useMemo(()=>Array.from({length:Math.round((gridEnd-gridStart)/86400000)+1},(_,index)=>addDays(gridStart,index)),[gridStart,gridEnd]);
  const {plans,error,load}=useCalendarRange(gridStart,gridEnd);
  const controls=<div className="flex flex-wrap gap-2"><Button variant="secondary" onClick={()=>setMonth(new Date(month.getFullYear(),month.getMonth()-1,1))}>Previous month</Button><Button variant="secondary" onClick={()=>setMonth(new Date(new Date().getFullYear(),new Date().getMonth(),1))}>Current month</Button><Button variant="secondary" onClick={()=>setMonth(new Date(month.getFullYear(),month.getMonth()+1,1))}>Next month</Button></div>;
  if(error)return <ErrorState message={error} retry={load}/>;
  return <><Card title={month.toLocaleDateString("en-IN",{month:"long",year:"numeric"})} action={controls}>{!plans?<LoadingState/>:<div className="overflow-x-auto"><div className="grid min-w-[980px] grid-cols-7 gap-px overflow-hidden rounded-lg border bg-slate-200">{["Mon","Tue","Wed","Thu","Fri","Sat","Sun"].map(day=><div key={day} className="bg-rail-950 p-2 text-center text-xs font-bold text-white">{day}</div>)}{days.map(day=><div key={dateKey(day)} className={`min-h-32 p-2 ${day.getMonth()===month.getMonth()?"bg-white":"bg-slate-50 text-slate-400"}`}><p className="mb-2 text-xs font-bold">{day.getDate()}</p>{plans.filter(plan=>sameDate(plan.start_time,day)).map(plan=><PlanChip key={plan.id} plan={plan} onClick={setSelected}/>)}</div>)}</div></div>}</Card><PlanDetails plan={selected} onClose={()=>setSelected(null)}/></>;
}

export function Conflicts() {
  const conflicts=useResource("conflicts"),bottlenecks=useResource("bottlenecks"); async function resolve(id){await api(`/conflicts/${id}/`,{method:"PATCH",body:JSON.stringify({resolved:true})});conflicts.load()}
  if(conflicts.error||bottlenecks.error)return <ErrorState message={conflicts.error||bottlenecks.error} retry={()=>{conflicts.load();bottlenecks.load()}}/>;if(!conflicts.rows||!bottlenecks.rows)return <LoadingState/>;
  return <div className="space-y-6"><Card title="Planning Conflicts"><Table rows={conflicts.rows} columns={[{key:"conflict_type",label:"Type",render:v=>v.replaceAll("_"," ")},{key:"description",label:"Description"},{key:"severity",label:"Severity",render:v=><Badge>{v}</Badge>},{key:"resolved",label:"Status",render:v=><Badge>{v?"RESOLVED":"OPEN"}</Badge>},{key:"id",label:"Action",render:(v,r)=>!r.resolved&&(canControl()?<Button variant="secondary" onClick={()=>resolve(v)}>Mark resolved</Button>:<span className="text-xs text-slate-500">Control Office only</span>)}]}/></Card><Card title="Explicit Section Bottlenecks"><Table rows={bottlenecks.rows} columns={[{key:"section",label:"Section"},{key:"date",label:"Date"},{key:"severity",label:"Severity",render:v=><Badge>{v}</Badge>},{key:"conflict_count",label:"Conflicts"},{key:"maintenance_demand",label:"Demand"},{key:"available_windows",label:"Available Windows"},{key:"reason",label:"Reason",render:v=>v.join(" · ")}]}/></Card></div>;
}

export function Alerts() {
  const {rows,error,load}=useResource("alerts"); async function read(id){await api(`/alerts/${id}/`,{method:"PATCH",body:JSON.stringify({is_read:true})});load()}
  if(error)return <ErrorState message={error} retry={load}/>;if(!rows)return <LoadingState/>;
  if(!rows.length)return <EmptyState message="No operational alerts are available."/>;
  return <div className="space-y-3">{rows.map(a=><Card key={a.id} className={a.is_read?"opacity-60":""}><div className="flex items-start justify-between gap-4"><div><div className="flex gap-2"><h3 className="font-bold">{a.title}</h3><Badge>{a.severity}</Badge></div><p className="mt-2 text-sm text-slate-600">{a.message}</p><p className="mt-2 text-xs text-slate-400">{formatDateTime(a.created_at)}</p></div>{!a.is_read&&canControl()&&<Button variant="secondary" onClick={()=>read(a.id)}>Mark read</Button>}</div></Card>)}</div>;
}

export function Execution() {
  const records=useResource("execution"),plans=useResource("block-plans");const [open,setOpen]=useState(false),[error,setError]=useState("");
  const [form,setForm]=useState({block_plan:"",actual_start:"",actual_end:"",status:"COMPLETED",remarks:""});
  async function create(e){e.preventDefault();try{await api("/execution/",{method:"POST",body:JSON.stringify(form)});setOpen(false);records.load()}catch(err){setError(err.message)}}
  if(records.error||plans.error)return <ErrorState message={records.error||plans.error}/>;if(!records.rows||!plans.rows)return <LoadingState/>;
  return <><Card title="Planned vs Actual Execution" action={canControl()&&<Button onClick={()=>setOpen(true)}>Record Execution</Button>}><Table rows={records.rows} columns={[{key:"block_plan",label:"Plan",render:v=>`#${v}`},{key:"planned_start",label:"Planned",render:(v,r)=><>{formatDateTime(v)}<br/><span className="text-xs">to {formatDateTime(r.planned_end)}</span></>},{key:"actual_start",label:"Actual",render:(v,r)=><>{formatDateTime(v)}<br/><span className="text-xs">to {formatDateTime(r.actual_end)}</span></>},{key:"variance_minutes",label:"Variance",render:v=><span className={v>0?"text-red-700":"text-emerald-700"}>{v>0?"+":""}{v} min</span>},{key:"status",label:"Status",render:v=><Badge>{v}</Badge>}]}/></Card><Modal open={open} onClose={()=>setOpen(false)} title="Record actual execution"><form onSubmit={create} className="space-y-4"><Field label="Block plan"><select required className={inputClass} value={form.block_plan} onChange={e=>setForm({...form,block_plan:e.target.value})}><option value="">Select…</option>{plans.rows.filter(p=>!records.rows.some(r=>r.block_plan===p.id)).map(p=><option key={p.id} value={p.id}>#{p.id} · {p.section_name} · {formatDateTime(p.start_time)}</option>)}</select></Field>{["actual_start","actual_end"].map(k=><Field key={k} label={k.replace("_"," ")}><input type="datetime-local" required className={inputClass} onChange={e=>setForm({...form,[k]:new Date(e.target.value).toISOString()})}/></Field>)}<Field label="Status"><select className={inputClass} value={form.status} onChange={e=>setForm({...form,status:e.target.value})}><option>COMPLETED</option><option>DELAYED</option><option>CANCELLED</option><option value="PARTIAL">PARTIALLY COMPLETED</option></select></Field><Field label="Remarks"><textarea className={inputClass} value={form.remarks} onChange={e=>setForm({...form,remarks:e.target.value})}/></Field>{error&&<p className="text-sm text-red-700">{error}</p>}<Button>Save execution result</Button></form></Modal></>;
}

export function SettingsPage() {
  const user=getStoredUser()||{};
  return <div className="grid gap-6 lg:grid-cols-2"><Card title="Operator Profile"><dl className="grid grid-cols-2 gap-4 text-sm"><dt className="text-slate-500">Username</dt><dd className="font-semibold">{user.username}</dd><dt className="text-slate-500">Role</dt><dd><Badge>{user.role}</Badge></dd><dt className="text-slate-500">Department</dt><dd>{user.department}</dd></dl></Card><Card title="Prototype Configuration"><p className="text-sm text-slate-600">Priority assumptions: Criticality 25%, Urgency 20%, Safety Risk 25%, Asset Impact 20%, Overdue 10%.</p><p className="mt-4 rounded-lg bg-amber-50 p-3 text-sm text-amber-800">Railway adapters are in simulated/local mode. No production railway system is connected.</p></Card></div>;
}
