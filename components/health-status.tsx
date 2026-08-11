"use client";

import { useCallback, useEffect, useState } from "react";

import { getApiHealth } from "@/lib/api";

type HealthState =
  | { status: "loading" }
  | { status: "ready"; service: string }
  | { status: "error"; message: string };

export function HealthStatus() {
  const [health, setHealth] = useState<HealthState>({ status: "loading" });

  const retryHealth = useCallback(async () => {
    setHealth({ status: "loading" });

    try {
      const result = await getApiHealth();
      setHealth({ status: "ready", service: result.service });
    } catch (error) {
      setHealth({
        status: "error",
        message: error instanceof Error ? error.message : "The API could not be reached.",
      });
    }
  }, []);

  useEffect(() => {
    const controller = new AbortController();

    void getApiHealth(controller.signal)
      .then((result) => setHealth({ status: "ready", service: result.service }))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") {
          return;
        }

        setHealth({
          status: "error",
          message: error instanceof Error ? error.message : "The API could not be reached.",
        });
      });

    return () => controller.abort();
  }, []);

  if (health.status === "loading") {
    return (
      <div aria-live="polite" className="rounded-2xl border border-white/10 bg-white/5 p-5">
        <div className="flex items-center gap-3">
          <span aria-hidden="true" className="size-2.5 animate-pulse rounded-full bg-amber-300" />
          <span className="text-sm font-semibold">Checking FastAPI…</span>
        </div>
      </div>
    );
  }

  if (health.status === "error") {
    return (
      <div aria-live="polite" className="rounded-2xl border border-rose-300/25 bg-rose-200/10 p-5">
        <p className="text-sm font-semibold text-rose-100">API unavailable</p>
        <p className="mt-1 text-xs leading-5 text-white/60">{health.message}</p>
        <button
          className="mt-4 min-h-11 rounded-xl bg-white px-4 py-2 text-sm font-semibold text-[#15271e] transition hover:bg-[#f3ffd1] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#d8ff62]"
          onClick={() => void retryHealth()}
          type="button"
        >
          Try again
        </button>
      </div>
    );
  }

  return (
    <div aria-live="polite" className="rounded-2xl border border-[#d8ff62]/25 bg-[#d8ff62]/10 p-5">
      <div className="flex items-center gap-3">
        <span aria-hidden="true" className="grid size-8 place-items-center rounded-full bg-[#d8ff62] text-[#15271e]">
          ✓
        </span>
        <div>
          <p className="text-sm font-semibold">API connected</p>
          <p className="mt-0.5 font-mono text-xs text-white/55">{health.service}</p>
        </div>
      </div>
    </div>
  );
}
