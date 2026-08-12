"use client";

import { FormEvent, useRef, useState } from "react";

import { authenticatedFetch } from "@/lib/auth/client";
import { confirmExtraction, linkMedia } from "@/lib/media";
import { ScreenshotImport } from "@/components/screenshot-import";

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

function summarizeWorkoutExtraction(data: Record<string, unknown>): string {
  const parts: string[] = [];
  if (typeof data.event_name === "string" && data.event_name) parts.push(data.event_name);
  if (typeof data.distance_km === "number") parts.push(`${data.distance_km} km`);
  if (typeof data.duration_seconds === "number") {
    const minutes = Math.floor(data.duration_seconds / 60);
    const seconds = Math.round(data.duration_seconds % 60);
    parts.push(`${minutes}:${String(seconds).padStart(2, "0")}`);
  }
  if (typeof data.occurred_at === "string" && data.occurred_at) parts.push(data.occurred_at);
  return parts.length > 0 ? parts.join(" · ") : "No details detected in the photo.";
}

type WorkoutFormProps = {
  onLogged: () => void;
};

export function WorkoutForm({ onLogged }: WorkoutFormProps) {
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const titleRef = useRef<HTMLInputElement>(null);
  const distanceRef = useRef<HTMLInputElement>(null);
  const durationRef = useRef<HTMLInputElement>(null);
  const occurredAtRef = useRef<HTMLInputElement>(null);
  const pendingMediaId = useRef<string | null>(null);
  const pendingExtractionResultId = useRef<string | null>(null);

  function handleMediaUploaded(mediaAssetId: string) {
    pendingMediaId.current = mediaAssetId;
  }

  function handleApplyExtraction(data: Record<string, unknown>, extractionResultId: string) {
    if (typeof data.event_name === "string" && data.event_name && titleRef.current) {
      titleRef.current.value = data.event_name;
    }
    if (typeof data.distance_km === "number" && distanceRef.current) {
      distanceRef.current.value = String(data.distance_km);
    }
    if (typeof data.duration_seconds === "number" && durationRef.current) {
      durationRef.current.value = String(Math.round(data.duration_seconds / 60));
    }
    if (typeof data.occurred_at === "string" && data.occurred_at && occurredAtRef.current) {
      const existing = occurredAtRef.current.value;
      const existingTime = existing.includes("T") ? existing.split("T")[1] : "12:00";
      occurredAtRef.current.value = `${data.occurred_at}T${existingTime}`;
    }
    pendingExtractionResultId.current = extractionResultId;
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);

    const form = event.currentTarget;
    const data = new FormData(form);
    const selectedCategories = categories
      .map((category) => category.slug)
      .filter((slug) => data.get(slug) === "on");

    const occurredAtLocal = String(data.get("occurredAt") ?? "");
    const usedExtraction = pendingExtractionResultId.current !== null;
    const payload = {
      occurred_at: occurredAtLocal ? new Date(occurredAtLocal).toISOString() : new Date().toISOString(),
      title: String(data.get("title") ?? "").trim(),
      activity_type: String(data.get("activityType") ?? "").trim(),
      category_slugs: selectedCategories,
      duration_minutes: data.get("durationMinutes") ? Number(data.get("durationMinutes")) : null,
      distance_km: data.get("distanceKm") ? Number(data.get("distanceKm")) : null,
      rpe: data.get("rpe") ? Number(data.get("rpe")) : null,
      visibility: String(data.get("visibility") ?? "team"),
      source: usedExtraction ? "image" : "manual",
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

      const workout: { id: string } = await response.json();
      const mediaId = pendingMediaId.current;
      if (mediaId) {
        try {
          await linkMedia(mediaId, "workout", workout.id);
          if (pendingExtractionResultId.current) {
            await confirmExtraction(mediaId, pendingExtractionResultId.current, payload);
          }
        } catch {
          setError("Workout saved, but the photo could not be attached.");
        }
      }

      pendingMediaId.current = null;
      pendingExtractionResultId.current = null;
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
      <ScreenshotImport
        extractionType="workout"
        label="Import from a screenshot (Parkrun, GPS watch, race timer)"
        onApply={handleApplyExtraction}
        onMediaUploaded={handleMediaUploaded}
        purpose="workout_evidence"
        summarize={summarizeWorkoutExtraction}
      />

      <div className="grid gap-4 sm:grid-cols-2">
        <label className="block text-sm font-semibold text-stone-700 sm:col-span-2">
          Title
          <input
            className="mt-2 min-h-12 w-full rounded-2xl border border-stone-300 px-4 text-base outline-none focus:border-[#789416] focus:ring-4 focus:ring-[#d8ff62]/30"
            maxLength={120}
            name="title"
            placeholder="Parkrun, MMA sparring, Rings strength…"
            ref={titleRef}
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
            ref={occurredAtRef}
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
            ref={durationRef}
            type="number"
          />
        </label>
        <label className="text-xs font-semibold text-stone-500">
          Distance, km
          <input
            className="mt-1 min-h-12 w-full rounded-2xl border border-stone-300 px-4 text-base"
            min={0}
            name="distanceKm"
            ref={distanceRef}
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
