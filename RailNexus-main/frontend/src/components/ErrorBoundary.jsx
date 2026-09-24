import React from "react";

export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { error: null };
  }

  static getDerivedStateFromError(error) {
    return { error };
  }

  componentDidCatch(error, info) {
    console.error("RailNexus runtime error", error, info);
  }

  render() {
    if (!this.state.error) return this.props.children;
    return <main className="grid min-h-screen place-items-center bg-slate-100 p-6">
      <section className="w-full max-w-2xl rounded-xl border border-red-200 bg-white p-8">
        <h1 className="text-2xl font-bold text-rail-950">RailNexus encountered an unexpected error.</h1>
        <p className="mt-3 text-sm text-slate-600">Reload the application and try again.</p>
        {import.meta.env.DEV&&<pre className="mt-5 max-h-64 overflow-auto rounded-lg bg-slate-950 p-4 text-xs text-slate-100">{this.state.error.stack||this.state.error.message}</pre>}
        <button onClick={()=>window.location.reload()} className="mt-5 rounded-lg bg-rail-900 px-4 py-2 text-sm font-semibold text-white hover:bg-rail-800">Retry</button>
      </section>
    </main>;
  }
}
