"use client";

import { FormEvent, useRef, useState } from "react";

import { authenticatedFetch } from "@/lib/auth/client";
import { uploadMedia } from "@/lib/media";

function nowForDatetimeLocal(): string {
  const now = new Date();
  now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
  return now.toISOString().slice(0, 16);
}

type MealFormProps = {
  onLogged: () => void;
};

export function MealForm({ onLogged }: MealFormProps) {
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const photoInputRef = useRef<HTMLInputElement>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);

    const form = event.currentTarget;
    const data = new FormData(form);
    const mealPhoto = photoInputRef.current?.files?.[0] ?? null;
    const occurredAtLocal = String(data.get("occurredAt") ?? "");

    const payload = {
      occurred_at: occurredAtLocal ? new Date(occurredAtLocal).toISOString() : new Date().toISOString(),
      meal_type: String(data.get("mealType") ?? "").trim() || null,
      description: String(data.get("description") ?? "").trim(),
      calories: data.get("calories") ? Number(data.get("calories")) : null,
      protein_g: data.get("proteinG") ? Number(data.get("proteinG")) : null,
      carbs_g: data.get("carbsG") ? Number(data.get("carbsG")) : null,
      fat_g: data.get("fatG") ? Number(data.get("fatG")) : null,
      visibility: String(data.get("visibility") ?? "private"),
      notes: String(data.get("notes") ?? "").trim() || null,
    };

    try {
      const response = await authenticatedFetch("/api/meals", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const body = await response.json().catch(() => null);
        const message = body?.error?.message;
        throw new Error(typeof message === "string" ? message : "Your meal could not be saved.");
      }

      if (mealPhoto) {
        const meal: { id: string } = await response.json();
        try {
          await uploadMedia(mealPhoto, {
            purpose: "meal_photo",
            entityType: "meal",
            entityId: meal.id,
          });
        } catch {
          setError("Meal saved, but the photo could not be uploaded.");
        }
      }

      form.reset();
      onLogged();
    } catch (submissionError) {
      setError(
        submissionError instanceof Error ? submissionError.message : "Your meal could not be saved.",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form className="space-y-6" onSubmit={handleSubmit}>
      <div className="grid gap-4 sm:grid-cols-2">
        <label className="block text-sm font-semibold text-stone-700 sm:col-span-2">
          What did you eat?
          <input
            className="mt-2 min-h-12 w-full rounded-2xl border border-stone-300 px-4 text-base outline-none focus:border-[#789416] focus:ring-4 focus:ring-[#d8ff62]/30"
            maxLength={500}
            name="description"
            placeholder="Oats, banana, protein shake"
            required
          />
        </label>

        <label className="block text-sm font-semibold text-stone-700">
          Meal type
          <input
            className="mt-2 min-h-12 w-full rounded-2xl border border-stone-300 px-4 text-base outline-none focus:border-[#789416] focus:ring-4 focus:ring-[#d8ff62]/30"
            list="meal-type-options"
            maxLength={30}
            name="mealType"
            placeholder="breakfast"
          />
          <datalist id="meal-type-options">
            <option value="breakfast" />
            <option value="lunch" />
            <option value="dinner" />
            <option value="snack" />
          </datalist>
        </label>

        <label className="block text-sm font-semibold text-stone-700">
          When
          <input
            className="mt-2 min-h-12 w-full rounded-2xl border border-stone-300 px-4 text-base outline-none focus:border-[#789416] focus:ring-4 focus:ring-[#d8ff62]/30"
            defaultValue={nowForDatetimeLocal()}
            name="occurredAt"
            required
            type="datetime-local"
          />
        </label>
      </div>

      <div className="grid grid-cols-4 gap-3">
        <label className="text-xs font-semibold text-stone-500">
          Calories
          <input className="mt-1 min-h-12 w-full rounded-2xl border border-stone-300 px-4 text-base" min={0} name="calories" type="number" />
        </label>
        <label className="text-xs font-semibold text-stone-500">
          Protein, g
          <input className="mt-1 min-h-12 w-full rounded-2xl border border-stone-300 px-4 text-base" min={0} name="proteinG" step="0.1" type="number" />
        </label>
        <label className="text-xs font-semibold text-stone-500">
          Carbs, g
          <input className="mt-1 min-h-12 w-full rounded-2xl border border-stone-300 px-4 text-base" min={0} name="carbsG" step="0.1" type="number" />
        </label>
        <label className="text-xs font-semibold text-stone-500">
          Fat, g
          <input className="mt-1 min-h-12 w-full rounded-2xl border border-stone-300 px-4 text-base" min={0} name="fatG" step="0.1" type="number" />
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
        <textarea className="mt-2 min-h-24 w-full rounded-2xl border border-stone-300 px-4 py-3 text-base" maxLength={2000} name="notes" />
      </label>

      <label className="block text-sm font-semibold text-stone-700">
        Meal photo <span className="font-normal text-stone-400">(optional)</span>
        <input
          accept="image/jpeg,image/png,image/webp,image/heic"
          capture="environment"
          className="mt-2 block w-full text-sm text-stone-600 file:mr-3 file:min-h-11 file:rounded-xl file:border-0 file:bg-[#f8ffe4] file:px-4 file:text-sm file:font-semibold file:text-[#567118]"
          name="mealPhoto"
          ref={photoInputRef}
          type="file"
        />
      </label>

      {error ? <p aria-live="polite" className="rounded-2xl bg-rose-50 px-4 py-3 text-sm text-rose-800">{error}</p> : null}

      <button
        className="min-h-12 w-full rounded-2xl bg-[#15271e] px-5 py-3 text-sm font-bold text-white disabled:cursor-wait disabled:opacity-60"
        disabled={isSubmitting}
        type="submit"
      >
        {isSubmitting ? "Logging meal…" : "Log meal"}
      </button>
    </form>
  );
}
