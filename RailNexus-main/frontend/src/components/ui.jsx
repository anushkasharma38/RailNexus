import { LoaderCircle, TriangleAlert } from "lucide-react";

export function Button({ children, variant = "primary", className = "", ...props }) {
  const styles = {
    primary: "bg-rail-900 text-white hover:bg-rail-800",
    secondary: "border border-slate-300 bg-white text-rail-900 hover:bg-slate-50",
    danger: "bg-signal-red text-white hover:opacity-90",
  };
  return <button className={`rounded-lg px-4 py-2 text-sm font-semibold transition disabled:cursor-not-allowed disabled:opacity-50 ${styles[variant]} ${className}`} {...props}>{children}</button>;
}

export function Card({ title, action, children, className = "" }) {
  return <section className={`rounded-xl border border-slate-200 bg-white shadow-panel ${className}`}>
    {(title || action) && <header className="flex items-center justify-between border-b border-slate-100 px-5 py-4">
      <h2 className="font-semibold text-rail-950">{title}</h2>{action}
    </header>}
    <div className="p-5">{children}</div>
  </section>;
}

export function Badge({ children, tone }) {
  const key = tone || String(children).toUpperCase();
  const styles = key.includes("CRITICAL") || key.includes("REJECT") || key.includes("CANCEL") || key.includes("CONFLICT")
    ? "bg-red-50 text-red-700 border-red-200"
    : key.includes("HIGH") || key.includes("PENDING") || key.includes("DELAY") || key.includes("DUE")
      ? "bg-amber-50 text-amber-800 border-amber-200"
      : key.includes("APPROV") || key.includes("COMPLETE") || key.includes("GOOD") || key.includes("AVAILABLE")
        ? "bg-emerald-50 text-emerald-700 border-emerald-200"
        : "bg-blue-50 text-blue-700 border-blue-200";
  return <span className={`inline-flex rounded-full border px-2.5 py-1 text-xs font-semibold ${styles}`}>{String(children).replaceAll("_", " ")}</span>;
}

export function StatCard({ label, value, icon: Icon, suffix = "" }) {
  return <Card><div className="flex items-start justify-between"><div><p className="text-sm text-slate-500">{label}</p><p className="mt-2 text-3xl font-bold text-rail-950">{value}{suffix}</p></div>{Icon && <div className="rounded-lg bg-blue-50 p-3 text-rail-700"><Icon size={22}/></div>}</div></Card>;
}

export function LoadingState() {
  return <div className="flex min-h-52 items-center justify-center gap-3 text-slate-500"><LoaderCircle className="animate-spin"/> Loading simulated operational data…</div>;
}

export function ErrorState({ message, retry }) {
  return <div className="rounded-xl border border-red-200 bg-red-50 p-6 text-red-800"><TriangleAlert className="mb-2"/><p>{message || "Unable to load data."}</p>{retry && <Button className="mt-4" onClick={retry}>Try again</Button>}</div>;
}

export function EmptyState({ message = "No records found." }) {
  return <div className="py-12 text-center text-sm text-slate-500">{message}</div>;
}

export function Table({ columns, rows, keyField = "id" }) {
  if (!rows?.length) return <EmptyState />;
  return <div className="scrollbar overflow-x-auto"><table className="w-full text-left text-sm"><thead><tr className="border-b border-slate-200 text-xs uppercase tracking-wide text-slate-500">{columns.map(c => <th className="px-3 py-3 font-semibold" key={c.key}>{c.label}</th>)}</tr></thead><tbody>{rows.map((row, index) => <tr className="border-b border-slate-100 last:border-0 hover:bg-slate-50" key={row[keyField] ?? index}>{columns.map(c => <td className="px-3 py-3.5" key={c.key}>{c.render ? c.render(row[c.key], row) : row[c.key] ?? "—"}</td>)}</tr>)}</tbody></table></div>;
}

export function Modal({ title, open, onClose, children }) {
  if (!open) return null;
  return <div className="fixed inset-0 z-50 grid place-items-center bg-rail-950/60 p-4" onMouseDown={onClose}><div className="max-h-[90vh] w-full max-w-xl overflow-auto rounded-xl bg-white shadow-2xl" onMouseDown={e => e.stopPropagation()}><header className="flex justify-between border-b p-5"><h2 className="font-semibold">{title}</h2><button onClick={onClose}>✕</button></header><div className="p-5">{children}</div></div></div>;
}

export function Field({ label, children }) {
  return <label className="block text-sm font-medium text-slate-700"><span className="mb-1.5 block">{label}</span>{children}</label>;
}

export const inputClass = "w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-sm outline-none focus:border-rail-700 focus:ring-2 focus:ring-blue-100";
