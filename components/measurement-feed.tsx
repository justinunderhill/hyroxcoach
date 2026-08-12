"use client";

import { forwardRef, useEffect, useImperativeHandle, useState } from "react";

import { authClient, authenticatedFetch } from "@/lib/auth/client";

type Measurement = {
  id: string;
  user_id: string;
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

function toDatetimeLocal(isoString: string): string {
  const date = new Date(isoString);
  date.setMinutes(date.getMinutes() - date.getTimezoneOffset());
  return date.toISOString().slice(0, 16);
}

type EditMeasurementFormProps = {
  measurement: Measurement;
  onCancel: () => void;
  onSaved: () => void;
};

function EditMeasurementForm({ measurement, onCancel, onSaved }: EditMeasurementFormProps) {
  const [occurredAt, setOccurredAt] = useState(toDatetimeLocal(measurement.occurred_at));
  const [weightKg, setWeightKg] = useState(measurement.weight_kg ?? "");
  const [waistCm, setWaistCm] = useState(measurement.waist_cm ?? "");
  const [restingHr, setRestingHr] = useState(measurement.resting_hr?.toString() ?? "");
  const [notes, setNotes] = useState(measurement.notes ?? "");
  const [visibility, setVisibility] = useState(measurement.visibility);
  const [error, setError] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);

  async function handleSave() {
    setError(null);
    setIsSaving(true);
    try {
      const response = await authenticatedFetch(`/api/measurements/${measurement.id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          occurred_at: new Date(occurredAt).toISOString(),
          weight_kg: weightKg ? Number(weightKg) : null,
          waist_cm: waistCm ? Number(waistCm) : null,
          resting_hr: restingHr ? Number(restingHr) : null,
          notes: notes.trim() || null,
          visibility,
        }),
      });
      if (!response.ok) {
        const body = await response.json().catch(() => null);
        const message = body?.error?.message;
        throw new Error(typeof message === "string" ? message : "This measurement could not be updated.");
      }
      onSaved();
    } catch (submissionError) {
      setError(
        submissionError instanceof Error ? submissionError.message : "This measurement could not be updated.",
      );
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <div className="mt-3 space-y-3 rounded-xl border border-stone-200 bg-[#fafaf7] p-3">
      <label className="block text-xs font-semibold text-stone-600">
        When
        <input
          className="mt-1 min-h-11 w-full rounded-xl border border-stone-300 px-3 text-sm"
          onChange={(event) => setOccurredAt(event.target.value)}
          type="datetime-local"
          value={occurredAt}
        />
      </label>
      <div className="grid grid-cols-3 gap-3">
        <label className="block text-xs font-semibold text-stone-600">
          Weight, kg
          <input
            className="mt-1 min-h-11 w-full rounded-xl border border-stone-300 px-3 text-sm"
            onChange={(event) => setWeightKg(event.target.value)}
            step="0.1"
            type="number"
            value={weightKg}
          />
        </label>
        <label className="block text-xs font-semibold text-stone-600">
          Waist, cm
          <input
            className="mt-1 min-h-11 w-full rounded-xl border border-stone-300 px-3 text-sm"
            onChange={(event) => setWaistCm(event.target.value)}
            step="0.1"
            type="number"
            value={waistCm}
          />
        </label>
        <label className="block text-xs font-semibold text-stone-600">
          Resting HR
          <input
            className="mt-1 min-h-11 w-full rounded-xl border border-stone-300 px-3 text-sm"
            onChange={(event) => setRestingHr(event.target.value)}
            type="number"
            value={restingHr}
          />
        </label>
      </div>
      <label className="block text-xs font-semibold text-stone-600">
        Notes
        <textarea
          className="mt-1 min-h-16 w-full rounded-xl border border-stone-300 px-3 py-2 text-sm"
          onChange={(event) => setNotes(event.target.value)}
          value={notes}
        />
      </label>
      <fieldset>
        <legend className="text-xs font-semibold text-stone-600">Visibility</legend>
        <div className="mt-1 flex gap-3">
          <label className="flex items-center gap-1.5 text-xs text-stone-700">
            <input checked={visibility === "private"} onChange={() => setVisibility("private")} type="radio" />
            Private
          </label>
          <label className="flex items-center gap-1.5 text-xs text-stone-700">
            <input checked={visibility === "team"} onChange={() => setVisibility("team")} type="radio" />
            Team
          </label>
        </div>
      </fieldset>
      {error ? <p className="rounded-xl bg-rose-50 px-3 py-2 text-xs text-rose-800">{error}</p> : null}
      <div className="flex gap-2">
        <button
          className="min-h-10 flex-1 rounded-xl bg-[#15271e] text-xs font-bold text-white disabled:cursor-wait disabled:opacity-60"
          disabled={isSaving}
          onClick={handleSave}
          type="button"
        >
          {isSaving ? "Saving…" : "Save changes"}
        </button>
        <button
          className="min-h-10 rounded-xl border border-stone-300 px-4 text-xs font-semibold text-stone-700"
          disabled={isSaving}
          onClick={onCancel}
          type="button"
        >
          Cancel
        </button>
      </div>
    </div>
  );
}

export const MeasurementFeed = forwardRef<MeasurementFeedHandle>(function MeasurementFeed(_props, ref) {
  const { data: session } = authClient.useSession();
  const [state, setState] = useState<FeedState>({ status: "loading" });
  const [reloadToken, setReloadToken] = useState(0);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [deleteErrorId, setDeleteErrorId] = useState<string | null>(null);

  useImperativeHandle(ref, () => ({
    refresh: () => setReloadToken((token) => token + 1),
  }));

  useEffect(() => {
    const controller = new AbortController();
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

  async function handleDelete(measurementId: string) {
    if (!window.confirm("Delete this measurement? This cannot be undone.")) return;
    setDeleteErrorId(null);
    setDeletingId(measurementId);
    try {
      const response = await authenticatedFetch(`/api/measurements/${measurementId}`, { method: "DELETE" });
      if (!response.ok && response.status !== 204) {
        throw new Error("This measurement could not be deleted.");
      }
      setReloadToken((token) => token + 1);
    } catch {
      setDeleteErrorId(measurementId);
    } finally {
      setDeletingId(null);
    }
  }

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

  const currentUserId = session?.user?.id;

  return (
    <ul className="space-y-3">
      {state.measurements.map((measurement) => {
        const isOwner = currentUserId !== undefined && measurement.user_id === currentUserId;
        const isEditing = editingId === measurement.id;
        return (
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
            {isOwner && isEditing ? (
              <EditMeasurementForm
                measurement={measurement}
                onCancel={() => setEditingId(null)}
                onSaved={() => {
                  setEditingId(null);
                  setReloadToken((token) => token + 1);
                }}
              />
            ) : null}
            {isOwner && !isEditing ? (
              <div className="mt-3 flex items-center gap-3">
                <button
                  className="text-xs font-semibold text-[#506b13] underline decoration-[#a4c72b] underline-offset-4"
                  onClick={() => setEditingId(measurement.id)}
                  type="button"
                >
                  Edit
                </button>
                <button
                  className="text-xs font-semibold text-rose-700 underline decoration-rose-300 underline-offset-4 disabled:opacity-50"
                  disabled={deletingId === measurement.id}
                  onClick={() => handleDelete(measurement.id)}
                  type="button"
                >
                  {deletingId === measurement.id ? "Deleting…" : "Delete"}
                </button>
              </div>
            ) : null}
            {deleteErrorId === measurement.id ? (
              <p className="mt-2 text-xs text-rose-700">This measurement could not be deleted.</p>
            ) : null}
          </li>
        );
      })}
    </ul>
  );
});
