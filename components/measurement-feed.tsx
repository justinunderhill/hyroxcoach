"use client";

import { forwardRef, useEffect, useImperativeHandle, useState } from "react";

import { authenticatedFetch } from "@/lib/auth/client";

type Measurement = {
  id: string;
  occurred_at: string;
  weight_kg: string | null;
  waist_cm: string | null;
  resting_hr: number | null;
  notes: string | null;
  visibility: "team" | "private";
};

type FeedState =
  | { status: "loading" }
  | { status: "ready"; measurements: Measurement[] }
  | { status: "error" };

export type MeasurementFeedHandle = {
  refresh: () => void;
};

function formatValues(measurement: Measurement): string {
  const parts: string[] = [];
  if (measurement.weight_kg) parts.push(`${Number(measurement.weight_kg)} kg`);
  if (measurement.waist_cm) parts.push(`waist ${Number(measurement.waist_cm)} cm`);
  if (measurement.resting_hr) parts.push(`RHR ${measurement.resting_hr}`);
  return parts.join(" · ");
}

export const MeasurementFeed = forwardRef<MeasurementFeedHandle>(function MeasurementFeed(_props, ref) {
  const [state, setState] = useState<FeedState>({ status: "loading" });
  const [reloadToken, setReloadToken] = useState(0);

  useImperativeHandle(ref, () => ({
    refresh: () => setReloadToken((token) => token + 1),
  }));

  useEffect(() => {
    const controller = new AbortController();
    setState({ status: "loading" });
    void authenticatedFetch("/api/measurements", { signal: controller.signal })
      .then(async (response) => {
        if (!response.ok) throw new Error();
        const measurements: Measurement[] = await response.json();
        setState({ status: "ready", measurements });
      })
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setState({ status: "error" });
      });
    return () => controller.abort();
  }, [reloadToken]);

  if (state.status === "loading") return <div className="h-40 animate-pulse rounded-3xl bg-stone-100" />;
  if (state.status === "error") {
    return <p className="rounded-3xl bg-rose-50 p-6 text-sm text-rose-800">Measurement history could not be loaded.</p>;
  }
  if (state.measurements.length === 0) {
    return (
      <div className="rounded-3xl border border-dashed border-stone-300 bg-white/50 p-6">
        <p className="text-sm text-stone-500">No measurements logged yet.</p>
      </div>
    );
  }

  return (
    <ul className="space-y-3">
      {state.measurements.map((measurement) => (
        <li className="rounded-2xl border border-stone-200 bg-white p-4" key={measurement.id}>
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="font-semibold text-[#15221b]">{formatValues(measurement) || "Note"}</p>
              <p className="mt-0.5 text-xs text-stone-500">
                {new Date(measurement.occurred_at).toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" })}
              </p>
            </div>
            <span className="shrink-0 rounded-full bg-[#f8ffe4] px-2.5 py-1 text-xs font-semibold text-[#567118]">
              {measurement.visibility === "team" ? "Team" : "Private"}
            </span>
          </div>
          {measurement.notes ? <p className="mt-2 text-sm text-stone-600">{measurement.notes}</p> : null}
        </li>
      ))}
    </ul>
  );
});
