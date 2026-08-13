"use client";

import { forwardRef, useEffect, useImperativeHandle, useState } from "react";

import { authenticatedFetch } from "@/lib/auth/client";

type DailyNutrition = {
  date: string;
  target: {
    calories_target: number | null;
    protein_g_target: string | null;
    carbs_g_target: string | null;
    fat_g_target: string | null;
  } | null;
  consumed: { calories: number; protein_g: number; carbs_g: number; fat_g: number };
  remaining: {
    calories: number | null;
    protein_g: number | null;
    carbs_g: number | null;
    fat_g: number | null;
  };
  meals: { id: string; description: string; occurred_at: string; calories: number | null }[];
};

type DailyState =
  | { status: "loading" }
  | { status: "ready"; nutrition: DailyNutrition }
  | { status: "error" };

export type DailyNutritionHandle = {
  refresh: () => void;
};

function macroRow(label: string, consumed: number, target: string | number | null, remaining: number | null) {
  const targetValue = target !== null ? Number(target) : null;
  const pct = targetValue ? Math.min(100, Math.round((consumed / targetValue) * 100)) : null;
  return (
    <div>
      <div className="flex items-baseline justify-between text-sm">
        <span className="font-semibold text-ink">{label}</span>
        <span className="text-muted">
          {consumed}
          {targetValue ? ` / ${targetValue}` : ""}
          {remaining !== null ? ` · ${remaining >= 0 ? `${remaining} left` : `${Math.abs(remaining)} over`}` : ""}
        </span>
      </div>
      {pct !== null ? (
        <div className="mt-1.5 h-2 overflow-hidden rounded-full bg-surface-2">
          <div className="h-full rounded-full bg-lime" style={{ width: `${pct}%` }} />
        </div>
      ) : null}
    </div>
  );
}

export const DailyNutritionCard = forwardRef<DailyNutritionHandle>(function DailyNutritionCard(_props, ref) {
  const [state, setState] = useState<DailyState>({ status: "loading" });
  const [reloadToken, setReloadToken] = useState(0);

  useImperativeHandle(ref, () => ({
    refresh: () => setReloadToken((token) => token + 1),
  }));

  useEffect(() => {
    const controller = new AbortController();
    setState({ status: "loading" });
    void authenticatedFetch("/api/nutrition/daily", { signal: controller.signal })
      .then(async (response) => {
        if (!response.ok) throw new Error();
        const nutrition: DailyNutrition = await response.json();
        setState({ status: "ready", nutrition });
      })
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setState({ status: "error" });
      });
    return () => controller.abort();
  }, [reloadToken]);

  if (state.status === "loading") return <div className="h-48 animate-pulse rounded-3xl bg-surface-2" />;
  if (state.status === "error") {
    return <p className="rounded-3xl bg-red/10 p-6 text-sm text-red">Nutrition for today could not be loaded.</p>;
  }

  const { nutrition } = state;

  return (
    <div className="rounded-3xl border border-line bg-surface p-6">
      <p className="text-xs font-semibold uppercase tracking-[0.18em] text-faint">Today</p>
      {nutrition.target === null ? (
        <p className="mt-2 text-sm text-muted">No target set yet — logged {nutrition.consumed.calories} kcal so far today.</p>
      ) : (
        <div className="mt-4 space-y-4">
          {macroRow("Calories", nutrition.consumed.calories, nutrition.target.calories_target, nutrition.remaining.calories)}
          {macroRow("Protein", nutrition.consumed.protein_g, nutrition.target.protein_g_target, nutrition.remaining.protein_g)}
          {macroRow("Carbs", nutrition.consumed.carbs_g, nutrition.target.carbs_g_target, nutrition.remaining.carbs_g)}
          {macroRow("Fat", nutrition.consumed.fat_g, nutrition.target.fat_g_target, nutrition.remaining.fat_g)}
        </div>
      )}
      <p className="mt-5 text-xs font-semibold uppercase tracking-[0.18em] text-faint">Meals today</p>
      {nutrition.meals.length === 0 ? (
        <p className="mt-2 text-sm text-muted">Nothing logged yet today.</p>
      ) : (
        <ul className="mt-2 space-y-1.5 text-sm text-muted">
          {nutrition.meals.map((meal) => (
            <li key={meal.id}>
              {meal.description}
              {meal.calories !== null ? ` — ${meal.calories} kcal` : ""}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
});
