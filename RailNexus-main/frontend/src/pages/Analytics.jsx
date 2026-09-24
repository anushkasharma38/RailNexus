import { useEffect, useState } from "react";
import { Bar, BarChart, CartesianGrid, Legend, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api } from "../services/api";
import { Card, ErrorState, LoadingState, StatCard } from "../components/ui";

export default function Analytics() {
  const [data,setData]=useState(null),[error,setError]=useState("");
  useEffect(()=>{api("/analytics/").then(setData).catch(e=>setError(e.message))},[]);
  if(error)return <ErrorState message={error}/>;if(!data)return <LoadingState/>;
  return <div className="space-y-6"><p className="rounded-lg border border-blue-200 bg-blue-50 p-3 text-sm text-blue-800">{data.source_label}</p><div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5"><StatCard label="Asset Availability" value={data.asset_availability} suffix="%"/><StatCard label="Block Utilization" value={data.block_utilization} suffix="%"/><StatCard label="Maintenance Completion" value={data.maintenance_completion} suffix="%"/><StatCard label="Open Conflicts" value={data.conflict_count}/><StatCard label="Avg. Schedule Variance" value={data.average_schedule_variance} suffix=" min"/></div><div className="grid gap-6 xl:grid-cols-2"><Card title="Section Asset Availability"><div className="h-80"><ResponsiveContainer><BarChart data={data.section_availability}><CartesianGrid strokeDasharray="3 3" vertical={false}/><XAxis dataKey="section"/><YAxis domain={[0,100]}/><Tooltip/><Bar dataKey="availability" fill="#185080" radius={[6,6,0,0]}/></BarChart></ResponsiveContainer></div></Card><Card title="Department Workload"><div className="h-80"><ResponsiveContainer><PieChart><Pie data={data.department_workload} dataKey="count" nameKey="department" innerRadius={65} outerRadius={105} fill="#185080" label/><Tooltip/><Legend/></PieChart></ResponsiveContainer></div></Card></div></div>;
}
