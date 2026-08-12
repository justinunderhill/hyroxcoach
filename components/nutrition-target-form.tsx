"use client";

import { FormEvent, useState } from "react";

import { authenticatedFetch } from "@/lib/auth/client";

type NutritionTargetFormProps = {
  onSaved: () => void;
};

export function NutritionTargetForm({ onSaved }: NutritionTargetFormProps) {
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);

    const form = event.currentTarget;
    const data = new FormData(form);

    const payload = {
      calories_target: data.get("caloriesTarget") ? Number(data.get("caloriesTarget")) : null,
      protein_g_target: data.get("proteinGTarget") ? Number(data.get("proteinGTarget")) : null,
      carbs_g_target: data.get("carbsGTarget") ? Number(data.get("carbsGTarget")) : null,
      fat_g_target: data.get("fatGTarget") ? Number(data.get("fatGTarget")) : null,
    };

    if (
      payload.calories_target === null &&
      payload.protein_g_target === null &&
      payload.carbs_g_target === null &&
      payload.fat_g_target === null
    ) {
      setError("Set at least one target value.");
      setIsSubmitting(false);
      return;
    }

    try {
      const response = await authenticatedFetch("/api/nutrition/targets", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const body = await response.json().catch(() => null);
        const message = body?.error?.message;
        throw new Error(typeof message === "string" ? message : "Your target could not be saved.");
      }

      onSaved();
    } catch (submissionError) {
      setError(
        submissionError instanceof Error ? submissionError.message : "Your target could not be saved.",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form className="space-y-4" onSubmit={handleSubmit}>
      <p className="text-xs font-semibold uppercase tracking-[0.18em] text-stone-400">Set new daily target</p>
      <div className="grid grid-cols-4 gap-3">
        <label className="text-xs font-semibold text-stone-500">
          Calories
          <input className="mt-1 min-h-12 w-full rounded-2xl border border-stone-300 px-4 text-base" min={0} name="caloriesTarget" type="number" />
        </label>
        <label className="text-xs font-semibold text-stone-500">
          Protein, g
          <input className="mt-1 min-h-12 w-full rounded-2xl border border-stone-300 px-4 text-base" min={0} name="proteinGTarget" step="0.1" type="number" />
        </label>
        <label className="text-xs font-semibold text-stone-500">
          Carbs, g
          <input className="mt-1 min-h-12 w-full rounded-2xl border border-stone-300 px-4 text-base" min={0} name="carbsGTarget" step="0.1" type="number" />
        </label>
        <label className="text-xs font-semibold text-stone-500">
          Fat, g
          <input className="mt-1 min-h-12 w-full rounded-2xl border border-stone-300 px-4 text-base" min={0} name="fatGTarget" step="0.1" type="number" />
        </label>
      </div>

      {error ? <p aria-live="polite" className="rounded-2xl bg-rose-50 px-4 py-3 text-sm text-rose-800">{error}</p> : null}

      <button
        className="min-h-11 rounded-xl border border-stone-300 px-4 text-sm font-semibold text-stone-700 disabled:cursor-wait disabled:opacity-60"
        disabled={isSubmitting}
        type="submit"
      >
        {isSubmitting ? "Saving…" : "Save target"}
      </button>
    </form>
  );
}
