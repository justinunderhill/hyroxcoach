"use client";

import { forwardRef, useEffect, useImperativeHandle, useState } from "react";

import { authenticatedFetch } from "@/lib/auth/client";

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
  visibility: "team" | "private";
};

type FeedState =
  | { status: "loading" }
  | { status: "ready"; meals: Meal[] }
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

export const MealFeed = forwardRef<MealFeedHandle>(function MealFeed(_props, ref) {
  const [state, setState] = useState<FeedState>({ status: "loading" });
  const [reloadToken, setReloadToken] = useState(0);

  useImperativeHandle(ref, () => ({
    refresh: () => setReloadToken((token) => token + 1),
  }));

  useEffect(() => {
    const controller = new AbortController();
    setState({ status: "loading" });
    void authenticatedFetch("/api/meals?limit=20", { signal: controller.signal })
      .then(async (response) => {
        if (!response.ok) throw new Error();
        const meals: Meal[] = await response.json();
        setState({ status: "ready", meals });
      })
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setState({ status: "error" });
      });
    return () => controller.abort();
  }, [reloadToken]);

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

  return (
    <ul className="space-y-3">
      {state.meals.map((meal) => (
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
        </li>
      ))}
    </ul>
  );
});
