"use client";

import { useRef } from "react";

import { DailyNutritionCard, DailyNutritionHandle } from "@/components/daily-nutrition";
import { NutritionTargetForm } from "@/components/nutrition-target-form";

export function NutritionClient() {
  const dailyRef = useRef<DailyNutritionHandle>(null);

  return (
    <div className="space-y-8">
      <DailyNutritionCard ref={dailyRef} />
      <div className="rounded-3xl border border-stone-200 bg-white p-6">
        <NutritionTargetForm onSaved={() => dailyRef.current?.refresh()} />
      </div>
    </div>
  );
}
