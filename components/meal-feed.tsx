"use client";

import { forwardRef, useEffect, useImperativeHandle, useState } from "react";

import { authClient, authenticatedFetch } from "@/lib/auth/client";
import { listMedia, MediaItem } from "@/lib/media";

type Meal = {
  id: string;
  user_id: string;
  occurred_at: string;
  meal_type: string | null;
  description: string;
  calories: number | null;
  protein_g: string | null;
  carbs_g: string | null;
  fat_g: string | null;
  notes: string | null;
  visibility: "team" | "private";
};

type FeedState =
  | { status: "loading" }
  | { status: "ready"; meals: Meal[]; mediaByMealId: Map<string, MediaItem[]> }
  | { status: "error" };

export type MealFeedHandle = {
  refresh: () => void;
};

function formatMacros(meal: Meal): string {
  const parts: string[] = [];
  if (meal.calories !== null) parts.push(`${meal.calories} kcal`);
  if (meal.protein_g) parts.push(`${Number(meal.protein_g)}g protein`);
  if (meal.carbs_g) parts.push(`${Number(meal.carbs_g)}g carbs`);
  if (meal.fat_g) parts.push(`${Number(meal.fat_g)}g fat`);
  return parts.join(" · ");
}

function toDatetimeLocal(isoString: string): string {
  const date = new Date(isoString);
  date.setMinutes(date.getMinutes() - date.getTimezoneOffset());
  return date.toISOString().slice(0, 16);
}

type EditMealFormProps = {
  meal: Meal;
  onCancel: () => void;
  onSaved: () => void;
};

function EditMealForm({ meal, onCancel, onSaved }: EditMealFormProps) {
  const [description, setDescription] = useState(meal.description);
  const [mealType, setMealType] = useState(meal.meal_type ?? "");
  const [occurredAt, setOccurredAt] = useState(toDatetimeLocal(meal.occurred_at));
  const [calories, setCalories] = useState(meal.calories?.toString() ?? "");
  const [proteinG, setProteinG] = useState(meal.protein_g ?? "");
  const [carbsG, setCarbsG] = useState(meal.carbs_g ?? "");
  const [fatG, setFatG] = useState(meal.fat_g ?? "");
  const [notes, setNotes] = useState(meal.notes ?? "");
  const [visibility, setVisibility] = useState(meal.visibility);
  const [error, setError] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);

  async function handleSave() {
    setError(null);
    setIsSaving(true);
    try {
      const response = await authenticatedFetch(`/api/meals/${meal.id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          description: description.trim(),
          meal_type: mealType.trim() || null,
          occurred_at: new Date(occurredAt).toISOString(),
          calories: calories ? Number(calories) : null,
          protein_g: proteinG ? Number(proteinG) : null,
          carbs_g: carbsG ? Number(carbsG) : null,
          fat_g: fatG ? Number(fatG) : null,
          notes: notes.trim() || null,
          visibility,
        }),
      });
      if (!response.ok) {
        const body = await response.json().catch(() => null);
        const message = body?.error?.message;
        throw new Error(typeof message === "string" ? message : "This meal could not be updated.");
      }
      onSaved();
    } catch (submissionError) {
      setError(submissionError instanceof Error ? submissionError.message : "This meal could not be updated.");
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <div className="mt-3 space-y-3 rounded-xl border border-stone-200 bg-[#fafaf7] p-3">
      <label className="block text-xs font-semibold text-stone-600">
        Description
        <input
          className="mt-1 min-h-11 w-full rounded-xl border border-stone-300 px-3 text-sm"
          onChange={(event) => setDescription(event.target.value)}
          value={description}
        />
      </label>
      <div className="grid grid-cols-2 gap-3">
        <label className="block text-xs font-semibold text-stone-600">
          Meal type
          <input
            className="mt-1 min-h-11 w-full rounded-xl border border-stone-300 px-3 text-sm"
            onChange={(event) => setMealType(event.target.value)}
            value={mealType}
          />
        </label>
        <label className="block text-xs font-semibold text-stone-600">
          When
          <input
            className="mt-1 min-h-11 w-full rounded-xl border border-stone-300 px-3 text-sm"
            onChange={(event) => setOccurredAt(event.target.value)}
            type="datetime-local"
            value={occurredAt}
          />
        </label>
      </div>
      <div className="grid grid-cols-4 gap-3">
        <label className="block text-xs font-semibold text-stone-600">
          Calories
          <input
            className="mt-1 min-h-11 w-full rounded-xl border border-stone-300 px-3 text-sm"
            onChange={(event) => setCalories(event.target.value)}
            type="number"
            value={calories}
          />
        </label>
        <label className="block text-xs font-semibold text-stone-600">
          Protein
          <input
            className="mt-1 min-h-11 w-full rounded-xl border border-stone-300 px-3 text-sm"
            onChange={(event) => setProteinG(event.target.value)}
            step="0.1"
            type="number"
            value={proteinG}
          />
        </label>
        <label className="block text-xs font-semibold text-stone-600">
          Carbs
          <input
            className="mt-1 min-h-11 w-full rounded-xl border border-stone-300 px-3 text-sm"
            onChange={(event) => setCarbsG(event.target.value)}
            step="0.1"
            type="number"
            value={carbsG}
          />
        </label>
        <label className="block text-xs font-semibold text-stone-600">
          Fat
          <input
            className="mt-1 min-h-11 w-full rounded-xl border border-stone-300 px-3 text-sm"
            onChange={(event) => setFatG(event.target.value)}
            step="0.1"
            type="number"
            value={fatG}
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

export const MealFeed = forwardRef<MealFeedHandle>(function MealFeed(_props, ref) {
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
    void authenticatedFetch("/api/meals?limit=20", { signal: controller.signal })
      .then(async (response) => {
        if (!response.ok) throw new Error();
        const meals: Meal[] = await response.json();
        const media = await listMedia(
          "meal",
          meals.map((meal) => meal.id),
          controller.signal,
        ).catch(() => []);
        const mediaByMealId = new Map<string, MediaItem[]>();
        for (const item of media) {
          const existing = mediaByMealId.get(item.entity_id) ?? [];
          existing.push(item);
          mediaByMealId.set(item.entity_id, existing);
        }
        setState({ status: "ready", meals, mediaByMealId });
      })
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setState({ status: "error" });
      });
    return () => controller.abort();
  }, [reloadToken]);

  async function handleDelete(mealId: string) {
    if (!window.confirm("Delete this meal? This cannot be undone.")) return;
    setDeleteErrorId(null);
    setDeletingId(mealId);
    try {
      const response = await authenticatedFetch(`/api/meals/${mealId}`, { method: "DELETE" });
      if (!response.ok && response.status !== 204) {
        throw new Error("This meal could not be deleted.");
      }
      setReloadToken((token) => token + 1);
    } catch {
      setDeleteErrorId(mealId);
    } finally {
      setDeletingId(null);
    }
  }

  if (state.status === "loading") return <div className="h-40 animate-pulse rounded-3xl bg-stone-100" />;
  if (state.status === "error") {
    return <p className="rounded-3xl bg-rose-50 p-6 text-sm text-rose-800">Meal history could not be loaded.</p>;
  }
  if (state.meals.length === 0) {
    return (
      <div className="rounded-3xl border border-dashed border-stone-300 bg-white/50 p-6">
        <p className="text-sm text-stone-500">No meals logged yet.</p>
      </div>
    );
  }

  const currentUserId = session?.user?.id;

  return (
    <ul className="space-y-3">
      {state.meals.map((meal) => {
        const isOwner = currentUserId !== undefined && meal.user_id === currentUserId;
        const isEditing = editingId === meal.id;
        return (
          <li className="rounded-2xl border border-stone-200 bg-white p-4" key={meal.id}>
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="font-semibold text-[#15221b]">
                  {meal.meal_type ? `${meal.meal_type[0].toUpperCase()}${meal.meal_type.slice(1)} — ` : ""}
                  {meal.description}
                </p>
                <p className="mt-0.5 text-xs text-stone-500">
                  {new Date(meal.occurred_at).toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" })}
                </p>
              </div>
              <span className="shrink-0 rounded-full bg-[#f8ffe4] px-2.5 py-1 text-xs font-semibold text-[#567118]">
                {meal.visibility === "team" ? "Team" : "Private"}
              </span>
            </div>
            {formatMacros(meal) ? <p className="mt-2 text-sm text-stone-600">{formatMacros(meal)}</p> : null}
            {(state.mediaByMealId.get(meal.id) ?? []).length > 0 ? (
              <div className="mt-3 flex gap-2">
                {(state.mediaByMealId.get(meal.id) ?? []).map((item) => (
                  <a href={item.view_url} key={item.media_asset.id} rel="noreferrer" target="_blank">
                    <img
                      alt="Meal photo"
                      className="size-16 rounded-xl border border-stone-200 object-cover"
                      src={item.view_url}
                    />
                  </a>
                ))}
              </div>
            ) : null}
            {isOwner && isEditing ? (
              <EditMealForm
                meal={meal}
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
                  onClick={() => setEditingId(meal.id)}
                  type="button"
                >
                  Edit
                </button>
                <button
                  className="text-xs font-semibold text-rose-700 underline decoration-rose-300 underline-offset-4 disabled:opacity-50"
                  disabled={deletingId === meal.id}
                  onClick={() => handleDelete(meal.id)}
                  type="button"
                >
                  {deletingId === meal.id ? "Deleting…" : "Delete"}
                </button>
              </div>
            ) : null}
            {deleteErrorId === meal.id ? (
              <p className="mt-2 text-xs text-rose-700">This meal could not be deleted.</p>
            ) : null}
          </li>
        );
      })}
    </ul>
  );
});
