"use client";

export default function SentryExamplePage() {
  return (
    <main className="grid min-h-screen place-items-center px-5 text-center">
      <button
        className="rounded-full bg-lime px-5 py-3 text-sm font-bold text-lime-ink"
        onClick={() => {
          throw new Error("Test error to verify Sentry error reporting is wired up (frontend).");
        }}
        type="button"
      >
        Throw test error
      </button>
    </main>
  );
}
