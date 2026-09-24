import { useEffect, useState } from "react";
import { api } from "../services/api";
import { Badge, Card, ErrorState, LoadingState, StatCard, Table } from "../components/ui";

function MetricGroup({title,children}) {
  return <Card title={title}><div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">{children}</div></Card>;
}

export default function Reports() {
  const [data,setData]=useState(null),[error,setError]=useState("");
  const load=()=>{setError("");return api("/reports/").then(setData).catch(e=>setError(e.message))};
  useEffect(()=>{load()},[]);
  if(error)return <ErrorState message={error} retry={load}/>;
  if(!data)return <LoadingState/>;
  return <div className="space-y-6">
    <p className="rounded-lg border border-blue-200 bg-blue-50 p-3 text-sm text-blue-800">{data.source_label} · Scope: {data.role_scope.replaceAll("_"," ")}</p>
    <MetricGroup title="Block Utilization Report"><StatCard label="Total Blocks" value={data.block_utilization.total_blocks}/><StatCard label="Approved Blocks" value={data.block_utilization.approved_blocks}/><StatCard label="Completed Blocks" value={data.block_utilization.completed_blocks}/><StatCard label="Average Utilization" value={data.block_utilization.utilization_percentage} suffix="%"/></MetricGroup>
    <div className="grid gap-6 xl:grid-cols-2">
      <MetricGroup title="Maintenance Report"><StatCard label="Total Tasks" value={data.maintenance.total_tasks}/><StatCard label="Completed" value={data.maintenance.completed}/><StatCard label="Pending" value={data.maintenance.pending}/><StatCard label="Overdue" value={data.maintenance.overdue}/></MetricGroup>
      <MetricGroup title="Conflict Report"><StatCard label="Total Conflicts" value={data.conflicts.total_conflicts}/><StatCard label="Critical" value={data.conflicts.critical}/><StatCard label="High" value={data.conflicts.high}/><StatCard label="Unresolved" value={data.conflicts.unresolved}/></MetricGroup>
    </div>
    <div className="grid gap-6 xl:grid-cols-2">
      <Card title="Maintenance by Department"><Table rows={data.maintenance.by_department} columns={[{key:"department",label:"Department",render:value=>value.replaceAll("_"," ")},{key:"count",label:"Tasks"}]}/></Card>
      <Card title={`Asset Availability · ${data.asset_availability.overall_availability}% Overall`}><Table rows={data.asset_availability.by_section} columns={[{key:"section",label:"Section"},{key:"availability",label:"Availability",render:value=>`${value}%`}]}/></Card>
    </div>
    <MetricGroup title="Planned vs Actual"><StatCard label="Avg. Schedule Variance" value={data.planned_vs_actual.average_schedule_variance} suffix=" min"/><StatCard label="Completed On Time" value={data.planned_vs_actual.completed_on_time}/><StatCard label="Delayed" value={data.planned_vs_actual.delayed}/><StatCard label="Cancelled" value={data.planned_vs_actual.cancelled}/></MetricGroup>
    <Card title="Explicit Bottleneck Report"><Table rows={data.bottlenecks} columns={[{key:"section",label:"Section"},{key:"date",label:"Date"},{key:"severity",label:"Severity",render:value=><Badge>{value}</Badge>},{key:"conflict_count",label:"Conflicts"},{key:"maintenance_demand",label:"Demand"},{key:"available_windows",label:"Available Windows"},{key:"reason",label:"Explanation",render:value=>value.join(" · ")}]}/></Card>
  </div>;
}
