"use client";

import { useRouter } from "next/navigation";
import { FormEvent, useMemo, useState } from "react";

import { authenticatedFetch } from "@/lib/auth/client";

const trainingDays = [
  "monday",
  "tuesday",
  "wednesday",
  "thursday",
  "friday",
  "saturday",
  "sunday",
] as const;

type OnboardingFormProps = {
  initialName: string;
};

export function OnboardingForm({ initialName }: OnboardingFormProps) {
  const router = useRouter();
  const detectedTimezone = useMemo(
    () => Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC",
    [],
  );
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);

    const form = new FormData(event.currentTarget);
    const fiveKmMinutes = Number(form.get("fiveKmMinutes") || 0);
    const fiveKmSeconds = Number(form.get("fiveKmSeconds") || 0);
    const baselineSeconds = fiveKmMinutes > 0 ? fiveKmMinutes * 60 + fiveKmSeconds : null;
    const selectedDays = trainingDays.filter((day) => form.get(day) === "on");

    const payload = {
      display_name: String(form.get("displayName") ?? "").trim(),
      timezone: String(form.get("timezone") ?? detectedTimezone),
      baseline_5k_seconds: baselineSeconds,
      training_days: selectedDays,
      training_notes: String(form.get("trainingNotes") ?? "").trim() || null,
      weight_kg: form.get("weightKg") ? Number(form.get("weightKg")) : null,
      waist_cm: form.get("waistCm") ? Number(form.get("waistCm")) : null,
    };

    try {
      const response = await authenticatedFetch("/api/me", {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const body = await response.json().catch(() => null);
        const message = body?.error?.message;
        throw new Error(typeof message === "string" ? message : "Your profile could not be saved.");
      }

      router.replace("/dashboard");
      router.refresh();
    } catch (submissionError) {
      setError(
        submissionError instanceof Error
          ? submissionError.message
          : "Your profile could not be saved.",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form className="mt-8 space-y-8" onSubmit={handleSubmit}>
      <div className="grid gap-5 sm:grid-cols-2">
        <label className="block text-sm font-semibold text-stone-700 sm:col-span-2">
          Display name
          <input
            autoComplete="name"
            className="mt-2 min-h-12 w-full rounded-2xl border border-stone-300 px-4 text-base outline-none focus:border-[#789416] focus:ring-4 focus:ring-[#d8ff62]/30"
            defaultValue={initialName}
            maxLength={80}
            name="displayName"
            required
          />
        </label>

        <label className="block text-sm font-semibold text-stone-700 sm:col-span-2">
          Timezone
          <input
            className="mt-2 min-h-12 w-full rounded-2xl border border-stone-300 px-4 text-base outline-none focus:border-[#789416] focus:ring-4 focus:ring-[#d8ff62]/30"
            defaultValue={detectedTimezone}
            maxLength={64}
            name="timezone"
            required
          />
        </label>
      </div>

      <fieldset>
        <legend className="text-sm font-semibold text-stone-700">When can you usually train?</legend>
        <div className="mt-3 grid grid-cols-2 gap-2 sm:grid-cols-4">
          {trainingDays.map((day) => (
            <label
              className="flex min-h-11 items-center gap-2 rounded-xl border border-stone-200 bg-[#fafaf7] px-3 text-sm capitalize text-stone-700"
              key={day}
            >
              <input className="size-4 accent-[#789416]" name={day} type="checkbox" />
              {day.slice(0, 3)}
            </label>
          ))}
        </div>
      </fieldset>

      <div>
        <p className="text-sm font-semibold text-stone-700">Optional 5 km baseline</p>
        <div className="mt-2 grid grid-cols-2 gap-3">
          <label className="text-xs text-stone-500">
            Minutes
            <input className="mt-1 min-h-12 w-full rounded-2xl border border-stone-300 px-4 text-base" min="1" name="fiveKmMinutes" type="number" />
          </label>
          <label className="text-xs text-stone-500">
            Seconds
            <input className="mt-1 min-h-12 w-full rounded-2xl border border-stone-300 px-4 text-base" max="59" min="0" name="fiveKmSeconds" type="number" />
          </label>
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <label className="text-sm font-semibold text-stone-700">
          Bodyweight, kg <span className="font-normal text-stone-400">(optional, private)</span>
          <input className="mt-2 min-h-12 w-full rounded-2xl border border-stone-300 px-4 text-base" max="400" min="20" name="weightKg" step="0.1" type="number" />
        </label>
        <label className="text-sm font-semibold text-stone-700">
          Waist, cm <span className="font-normal text-stone-400">(optional, private)</span>
          <input className="mt-2 min-h-12 w-full rounded-2xl border border-stone-300 px-4 text-base" max="250" min="30" name="waistCm" step="0.1" type="number" />
        </label>
      </div>

      <label className="block text-sm font-semibold text-stone-700">
        Availability notes <span className="font-normal text-stone-400">(optional)</span>
        <textarea className="mt-2 min-h-24 w-full rounded-2xl border border-stone-300 px-4 py-3 text-base" maxLength={500} name="trainingNotes" placeholder="For example: weekday mornings, longer session on Saturday" />
      </label>

      {error ? <p aria-live="polite" className="rounded-2xl bg-rose-50 px-4 py-3 text-sm text-rose-800">{error}</p> : null}

      <button className="min-h-12 w-full rounded-2xl bg-[#15271e] px-5 py-3 text-sm font-bold text-white disabled:cursor-wait disabled:opacity-60" disabled={isSubmitting} type="submit">
        {isSubmitting ? "Saving profile…" : "Continue to dashboard"}
      </button>
    </form>
  );
}
