export default function OfflinePage() {
  return (
    <main className="grid min-h-screen place-items-center bg-slate-900 px-6 text-center text-white">
      <div>
        <p className="text-sm font-semibold uppercase tracking-[0.2em] text-emerald-300">
          SwarmDining
        </p>
        <h1 className="mt-4 text-3xl font-bold">You are offline</h1>
        <p className="mt-3 text-slate-300">Reconnecting…</p>
      </div>
    </main>
  );
}
