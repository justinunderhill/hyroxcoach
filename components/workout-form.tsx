"use client";

import { FormEvent, useRef, useState } from "react";

import { authenticatedFetch } from "@/lib/auth/client";
import { uploadMedia } from "@/lib/media";

const categories = [
  { slug: "running", label: "Running" },
  { slug: "skierg", label: "SkiErg" },
  { slug: "sled_push", label: "Sled push" },
  { slug: "sled_pull", label: "Sled pull" },
  { slug: "burpee_broad_jumps", label: "Burpee broad jumps" },
  { slug: "row", label: "Row" },
  { slug: "farmers_carry", label: "Farmers carry" },
  { slug: "sandbag_lunges", label: "Sandbag lunges" },
  { slug: "wall_balls", label: "Wall balls" },
  { slug: "strength", label: "Strength" },
  { slug: "mma_combat", label: "MMA / Combat" },
  { slug: "mobility", label: "Mobility" },
  { slug: "recovery", label: "Recovery" },
  { slug: "walking", label: "Walking" },
  { slug: "other", label: "Other" },
] as const;

function nowForDatetimeLocal(): string {
  const now = new Date();
  now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
  return now.toISOString().slice(0, 16);
}

type WorkoutFormProps = {
  onLogged: () => void;
};

export function WorkoutForm({ onLogged }: WorkoutFormProps) {
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const evidenceInputRef = useRef<HTMLInputElement>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);

    const form = event.currentTarget;
    const data = new FormData(form);
    const evidencePhoto = evidenceInputRef.current?.files?.[0] ?? null;
    const selectedCategories = categories
      .map((category) => category.slug)
      .filter((slug) => data.get(slug) === "on");

    const occurredAtLocal = String(data.get("occurredAt") ?? "");
    const payload = {
      occurred_at: occurredAtLocal ? new Date(occurredAtLocal).toISOString() : new Date().toISOString(),
      title: String(data.get("title") ?? "").trim(),
      activity_type: String(data.get("activityType") ?? "").trim(),
      category_slugs: selectedCategories,
      duration_minutes: data.get("durationMinutes") ? Number(data.get("durationMinutes")) : null,
      distance_km: data.get("distanceKm") ? Number(data.get("distanceKm")) : null,
      rpe: data.get("rpe") ? Number(data.get("rpe")) : null,
      visibility: String(data.get("visibility") ?? "team"),
      notes: String(data.get("notes") ?? "").trim() || null,
    };

    try {
      const response = await authenticatedFetch("/api/workouts", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const body = await response.json().catch(() => null);
        const message = body?.error?.message;
        throw new Error(typeof message === "string" ? message : "Your workout could not be saved.");
      }

      if (evidencePhoto) {
        const workout: { id: string } = await response.json();
        try {
          await uploadMedia(evidencePhoto, {
            purpose: "workout_evidence",
            entityType: "workout",
            entityId: workout.id,
          });
        } catch {
          setError("Workout saved, but the photo could not be uploaded.");
        }
      }

      form.reset();
      onLogged();
    } catch (submissionError) {
      setError(
        submissionError instanceof Error
          ? submissionError.message
          : "Your workout could not be saved.",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form className="space-y-6" onSubmit={handleSubmit}>
      <div className="grid gap-4 sm:grid-cols-2">
        <label className="block text-sm font-semibold text-stone-700 sm:col-span-2">
          Title
          <input
            className="mt-2 min-h-12 w-full rounded-2xl border border-stone-300 px-4 text-base outline-none focus:border-[#789416] focus:ring-4 focus:ring-[#d8ff62]/30"
            maxLength={120}
            name="title"
            placeholder="Parkrun, MMA sparring, Rings strength…"
            required
          />
        </label>

        <label className="block text-sm font-semibold text-stone-700">
          Activity type
          <input
            className="mt-2 min-h-12 w-full rounded-2xl border border-stone-300 px-4 text-base outline-none focus:border-[#789416] focus:ring-4 focus:ring-[#d8ff62]/30"
            list="activity-type-options"
            maxLength={60}
            name="activityType"
            placeholder="running"
            required
          />
          <datalist id="activity-type-options">
            <option value="running" />
            <option value="hyrox_simulation" />
            <option value="strength" />
            <option value="mma" />
            <option value="walking" />
            <option value="mobility" />
            <option value="other" />
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

      <fieldset>
        <legend className="text-sm font-semibold text-stone-700">HYROX categories</legend>
        <div className="mt-3 grid grid-cols-2 gap-2 sm:grid-cols-3">
          {categories.map((category) => (
            <label
              className="flex min-h-11 items-center gap-2 rounded-xl border border-stone-200 bg-[#fafaf7] px-3 text-sm text-stone-700"
              key={category.slug}
            >
              <input className="size-4 accent-[#789416]" name={category.slug} type="checkbox" />
              {category.label}
            </label>
          ))}
        </div>
      </fieldset>

      <div className="grid grid-cols-3 gap-3">
        <label className="text-xs font-semibold text-stone-500">
          Minutes
          <input
            className="mt-1 min-h-12 w-full rounded-2xl border border-stone-300 px-4 text-base"
            max={1440}
            min={1}
            name="durationMinutes"
            type="number"
          />
        </label>
        <label className="text-xs font-semibold text-stone-500">
          Distance, km
          <input
            className="mt-1 min-h-12 w-full rounded-2xl border border-stone-300 px-4 text-base"
            min={0}
            name="distanceKm"
            step="0.01"
            type="number"
          />
        </label>
        <label className="text-xs font-semibold text-stone-500">
          RPE
          <input
            className="mt-1 min-h-12 w-full rounded-2xl border border-stone-300 px-4 text-base"
            max={10}
            min={1}
            name="rpe"
            type="number"
          />
        </label>
      </div>

      <fieldset>
        <legend className="text-sm font-semibold text-stone-700">Visibility</legend>
        <div className="mt-2 flex gap-3">
          <label className="flex min-h-11 items-center gap-2 rounded-xl border border-stone-200 bg-[#fafaf7] px-3 text-sm text-stone-700">
            <input defaultChecked className="accent-[#789416]" name="visibility" type="radio" value="team" />
            Share with team
          </label>
          <label className="flex min-h-11 items-center gap-2 rounded-xl border border-stone-200 bg-[#fafaf7] px-3 text-sm text-stone-700">
            <input className="accent-[#789416]" name="visibility" type="radio" value="private" />
            Private
          </label>
        </div>
      </fieldset>

      <label className="block text-sm font-semibold text-stone-700">
        Notes <span className="font-normal text-stone-400">(optional)</span>
        <textarea
          className="mt-2 min-h-24 w-full rounded-2xl border border-stone-300 px-4 py-3 text-base"
          maxLength={2000}
          name="notes"
        />
      </label>

      <label className="block text-sm font-semibold text-stone-700">
        Evidence photo <span className="font-normal text-stone-400">(optional)</span>
        <input
          accept="image/jpeg,image/png,image/webp,image/heic"
          capture="environment"
          className="mt-2 block w-full text-sm text-stone-600 file:mr-3 file:min-h-11 file:rounded-xl file:border-0 file:bg-[#f8ffe4] file:px-4 file:text-sm file:font-semibold file:text-[#567118]"
          name="evidencePhoto"
          ref={evidenceInputRef}
          type="file"
        />
      </label>

      {error ? <p aria-live="polite" className="rounded-2xl bg-rose-50 px-4 py-3 text-sm text-rose-800">{error}</p> : null}

      <button
        className="min-h-12 w-full rounded-2xl bg-[#15271e] px-5 py-3 text-sm font-bold text-white disabled:cursor-wait disabled:opacity-60"
        disabled={isSubmitting}
        type="submit"
      >
        {isSubmitting ? "Logging workout…" : "Log workout"}
      </button>
    </form>
  );
}
