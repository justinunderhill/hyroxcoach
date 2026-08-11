"use client";

import { FormEvent, useState } from "react";

import { authenticatedFetch } from "@/lib/auth/client";

type MeasurementFormProps = {
  onLogged: () => void;
};

export function MeasurementForm({ onLogged }: MeasurementFormProps) {
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);

    const form = event.currentTarget;
    const data = new FormData(form);

    const payload = {
      weight_kg: data.get("weightKg") ? Number(data.get("weightKg")) : null,
      waist_cm: data.get("waistCm") ? Number(data.get("waistCm")) : null,
      resting_hr: data.get("restingHr") ? Number(data.get("restingHr")) : null,
      notes: String(data.get("notes") ?? "").trim() || null,
      visibility: String(data.get("visibility") ?? "private"),
    };

    if (!payload.weight_kg && !payload.waist_cm && !payload.notes) {
      setError("Add a weight, waist measurement or note.");
      setIsSubmitting(false);
      return;
    }

    try {
      const response = await authenticatedFetch("/api/measurements", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const body = await response.json().catch(() => null);
        const message = body?.error?.message;
        throw new Error(typeof message === "string" ? message : "Your measurement could not be saved.");
      }

      form.reset();
      onLogged();
    } catch (submissionError) {
      setError(
        submissionError instanceof Error
          ? submissionError.message
          : "Your measurement could not be saved.",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form className="space-y-6" onSubmit={handleSubmit}>
      <div className="grid grid-cols-3 gap-3">
        <label className="text-xs font-semibold text-stone-500">
          Bodyweight, kg
          <input className="mt-1 min-h-12 w-full rounded-2xl border border-stone-300 px-4 text-base" max={400} min={20} name="weightKg" step="0.1" type="number" />
        </label>
        <label className="text-xs font-semibold text-stone-500">
          Waist, cm
          <input className="mt-1 min-h-12 w-full rounded-2xl border border-stone-300 px-4 text-base" max={250} min={30} name="waistCm" step="0.1" type="number" />
        </label>
        <label className="text-xs font-semibold text-stone-500">
          Resting HR
          <input className="mt-1 min-h-12 w-full rounded-2xl border border-stone-300 px-4 text-base" max={250} min={20} name="restingHr" type="number" />
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

      <label className="block text-sm font-semibold text-stone-700">
        Notes <span className="font-normal text-stone-400">(optional)</span>
        <textarea className="mt-2 min-h-20 w-full rounded-2xl border border-stone-300 px-4 py-3 text-base" maxLength={500} name="notes" />
      </label>

      {error ? <p aria-live="polite" className="rounded-2xl bg-rose-50 px-4 py-3 text-sm text-rose-800">{error}</p> : null}

      <button
        className="min-h-12 w-full rounded-2xl bg-[#15271e] px-5 py-3 text-sm font-bold text-white disabled:cursor-wait disabled:opacity-60"
        disabled={isSubmitting}
        type="submit"
      >
        {isSubmitting ? "Saving…" : "Log measurement"}
      </button>
    </form>
  );
}
