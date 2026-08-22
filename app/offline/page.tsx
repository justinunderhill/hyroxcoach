export default function OfflinePage() {
  return (
    <main className="grid min-h-screen place-items-center px-5 text-center">
      <div>
        <p className="font-mono text-xs font-semibold uppercase tracking-[0.2em] text-lime">
          You&apos;re offline
        </p>
        <h1 className="mt-2 text-2xl font-semibold text-ink">No connection right now</h1>
        <p className="mt-2 text-sm text-muted">
          This page needs a connection to load. Reconnect and try again.
        </p>
      </div>
    </main>
  );
}
