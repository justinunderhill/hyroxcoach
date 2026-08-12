"use client";

import { FormEvent, useState } from "react";

import { authenticatedFetch } from "@/lib/auth/client";

function todayLocalDate(): string {
  const now = new Date();
  now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
  return now.toISOString().slice(0, 10);
}

type StepsFormProps = {
  onSaved: () => void;
};

export function StepsForm({ onSaved }: StepsFormProps) {
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);

    const form = event.currentTarget;
    const data = new FormData(form);
    const stepDate = String(data.get("date") ?? todayLocalDate());

    const payload = {
      steps: Number(data.get("steps") ?? 0),
      source: String(data.get("source") ?? "manual"),
      visibility: String(data.get("visibility") ?? "private"),
    };

    try {
      const response = await authenticatedFetch(`/api/steps/${stepDate}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const body = await response.json().catch(() => null);
        const message = body?.error?.message;
        throw new Error(typeof message === "string" ? message : "Your steps could not be saved.");
      }

      onSaved();
    } catch (submissionError) {
      setError(
        submissionError instanceof Error ? submissionError.message : "Your steps could not be saved.",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form className="space-y-4" onSubmit={handleSubmit}>
      <div className="grid grid-cols-2 gap-3">
        <label className="text-xs font-semibold text-stone-500">
          Date
          <input className="mt-1 min-h-12 w-full rounded-2xl border border-stone-300 px-4 text-base" defaultValue={todayLocalDate()} name="date" type="date" />
        </label>
        <label className="text-xs font-semibold text-stone-500">
          Steps
          <input className="mt-1 min-h-12 w-full rounded-2xl border border-stone-300 px-4 text-base" max={200000} min={0} name="steps" required type="number" />
        </label>
      </div>

      <fieldset>
        <legend className="text-sm font-semibold text-stone-700">Visibility</legend>
        <div className="mt-2 flex gap-3">
          <label className="flex min-h-11 items-center gap-2 rounded-xl border border-stone-200 bg-[#fafaf7] px-3 text-sm text-stone-700">
            <input defaultChecked className="accent-[#789416]" name="visibility" type="radio" value="private" />
            Private
          </label>
          <label className="flex min-h-11 items-center gap-2 rounded-xl border border-stone-200 bg-[#fafaf7] px-3 text-sm text-stone-700">
            <input className="accent-[#789416]" name="visibility" type="radio" value="team" />
            Share with team
          </label>
        </div>
      </fieldset>

      <input name="source" type="hidden" value="manual" />

      {error ? <p aria-live="polite" className="rounded-2xl bg-rose-50 px-4 py-3 text-sm text-rose-800">{error}</p> : null}

      <button
        className="min-h-12 w-full rounded-2xl bg-[#15271e] px-5 py-3 text-sm font-bold text-white disabled:cursor-wait disabled:opacity-60"
        disabled={isSubmitting}
        type="submit"
      >
        {isSubmitting ? "Saving…" : "Save steps"}
      </button>
    </form>
  );
}
