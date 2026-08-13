"use client";

import { FormEvent, useRef, useState } from "react";

import { authenticatedFetch } from "@/lib/auth/client";
import { confirmExtraction, linkMedia } from "@/lib/media";
import { ScreenshotImport } from "@/components/screenshot-import";

function nowForDatetimeLocal(): string {
  const now = new Date();
  now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
  return now.toISOString().slice(0, 16);
}

function summarizeMealExtraction(data: Record<string, unknown>): string {
  const foods = Array.isArray(data.likely_foods) ? (data.likely_foods as string[]) : [];
  const parts: string[] = [];
  if (foods.length > 0) parts.push(foods.join(", "));
  if (
    typeof data.estimated_calories_low === "number" &&
    typeof data.estimated_calories_high === "number"
  ) {
    parts.push(`~${data.estimated_calories_low}–${data.estimated_calories_high} kcal (estimate)`);
  }
  return parts.length > 0 ? parts.join(" · ") : "No details detected in the photo.";
}

type MealFormProps = {
  onLogged: () => void;
};

export function MealForm({ onLogged }: MealFormProps) {
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const descriptionRef = useRef<HTMLInputElement>(null);
  const mealTypeRef = useRef<HTMLInputElement>(null);
  const caloriesRef = useRef<HTMLInputElement>(null);
  const pendingMediaId = useRef<string | null>(null);
  const pendingExtractionResultId = useRef<string | null>(null);

  function handleMediaUploaded(mediaAssetId: string) {
    pendingMediaId.current = mediaAssetId;
  }

  function handleApplyExtraction(data: Record<string, unknown>, extractionResultId: string) {
    const foods = Array.isArray(data.likely_foods) ? (data.likely_foods as string[]) : [];
    if (foods.length > 0 && descriptionRef.current) {
      descriptionRef.current.value = foods.join(", ");
    }
    if (typeof data.meal_type === "string" && data.meal_type && mealTypeRef.current) {
      mealTypeRef.current.value = data.meal_type;
    }
    const low = typeof data.estimated_calories_low === "number" ? data.estimated_calories_low : null;
    const high = typeof data.estimated_calories_high === "number" ? data.estimated_calories_high : null;
    if (low !== null && high !== null && caloriesRef.current) {
      caloriesRef.current.value = String(Math.round((low + high) / 2));
    }
    pendingExtractionResultId.current = extractionResultId;
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);

    const form = event.currentTarget;
    const data = new FormData(form);
    const occurredAtLocal = String(data.get("occurredAt") ?? "");
    const usedExtraction = pendingExtractionResultId.current !== null;

    const payload = {
      occurred_at: occurredAtLocal ? new Date(occurredAtLocal).toISOString() : new Date().toISOString(),
      meal_type: String(data.get("mealType") ?? "").trim() || null,
      description: String(data.get("description") ?? "").trim(),
      calories: data.get("calories") ? Number(data.get("calories")) : null,
      protein_g: data.get("proteinG") ? Number(data.get("proteinG")) : null,
      carbs_g: data.get("carbsG") ? Number(data.get("carbsG")) : null,
      fat_g: data.get("fatG") ? Number(data.get("fatG")) : null,
      nutrition_is_estimated: usedExtraction,
      visibility: String(data.get("visibility") ?? "private"),
      source: usedExtraction ? "image" : "manual",
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

      const meal: { id: string } = await response.json();
      const mediaId = pendingMediaId.current;
      if (mediaId) {
        try {
          await linkMedia(mediaId, "meal", meal.id);
          if (pendingExtractionResultId.current) {
            await confirmExtraction(mediaId, pendingExtractionResultId.current, payload);
          }
        } catch {
          setError("Meal saved, but the photo could not be attached.");
        }
      }

      pendingMediaId.current = null;
      pendingExtractionResultId.current = null;
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
      <ScreenshotImport
        extractionType="meal"
        label="Import from a meal photo"
        onApply={handleApplyExtraction}
        onMediaUploaded={handleMediaUploaded}
        purpose="meal_photo"
        summarize={summarizeMealExtraction}
      />

      <div className="grid gap-4 sm:grid-cols-2">
        <label className="block text-sm font-semibold text-ink sm:col-span-2">
          What did you eat?
          <input
            className="mt-2 min-h-12 w-full rounded-2xl border border-line-strong px-4 text-base outline-none focus:border-lime focus:ring-4 focus:ring-lime/30"
            maxLength={500}
            name="description"
            placeholder="Oats, banana, protein shake"
            ref={descriptionRef}
            required
          />
        </label>

        <label className="block text-sm font-semibold text-ink">
          Meal type
          <input
            className="mt-2 min-h-12 w-full rounded-2xl border border-line-strong px-4 text-base outline-none focus:border-lime focus:ring-4 focus:ring-lime/30"
            list="meal-type-options"
            maxLength={30}
            name="mealType"
            placeholder="breakfast"
            ref={mealTypeRef}
          />
          <datalist id="meal-type-options">
            <option value="breakfast" />
            <option value="lunch" />
            <option value="dinner" />
            <option value="snack" />
          </datalist>
        </label>

        <label className="block text-sm font-semibold text-ink">
          When
          <input
            className="mt-2 min-h-12 w-full rounded-2xl border border-line-strong px-4 text-base outline-none focus:border-lime focus:ring-4 focus:ring-lime/30"
            defaultValue={nowForDatetimeLocal()}
            name="occurredAt"
            required
            type="datetime-local"
          />
        </label>
      </div>

      <div className="grid grid-cols-4 gap-3">
        <label className="text-xs font-semibold text-muted">
          Calories
          <input className="mt-1 min-h-12 w-full rounded-2xl border border-line-strong px-4 text-base" min={0} name="calories" ref={caloriesRef} type="number" />
        </label>
        <label className="text-xs font-semibold text-muted">
          Protein, g
          <input className="mt-1 min-h-12 w-full rounded-2xl border border-line-strong px-4 text-base" min={0} name="proteinG" step="0.1" type="number" />
        </label>
        <label className="text-xs font-semibold text-muted">
          Carbs, g
          <input className="mt-1 min-h-12 w-full rounded-2xl border border-line-strong px-4 text-base" min={0} name="carbsG" step="0.1" type="number" />
        </label>
        <label className="text-xs font-semibold text-muted">
          Fat, g
          <input className="mt-1 min-h-12 w-full rounded-2xl border border-line-strong px-4 text-base" min={0} name="fatG" step="0.1" type="number" />
        </label>
      </div>

      <fieldset>
        <legend className="text-sm font-semibold text-ink">Visibility</legend>
        <div className="mt-2 flex gap-3">
          <label className="flex min-h-11 items-center gap-2 rounded-xl border border-line bg-surface-2 px-3 text-sm text-ink">
            <input defaultChecked className="accent-lime" name="visibility" type="radio" value="private" />
            Private
          </label>
          <label className="flex min-h-11 items-center gap-2 rounded-xl border border-line bg-surface-2 px-3 text-sm text-ink">
            <input className="accent-lime" name="visibility" type="radio" value="team" />
            Share with team
          </label>
        </div>
      </fieldset>

      <label className="block text-sm font-semibold text-ink">
        Notes <span className="font-normal text-faint">(optional)</span>
        <textarea className="mt-2 min-h-24 w-full rounded-2xl border border-line-strong px-4 py-3 text-base" maxLength={2000} name="notes" />
      </label>

      {error ? <p aria-live="polite" className="rounded-2xl bg-red/10 px-4 py-3 text-sm text-red">{error}</p> : null}

      <button
        className="min-h-12 w-full rounded-2xl bg-lime px-5 py-3 text-sm font-bold text-lime-ink disabled:cursor-wait disabled:opacity-60"
        disabled={isSubmitting}
        type="submit"
      >
        {isSubmitting ? "Logging meal…" : "Log meal"}
      </button>
    </form>
  );
}
