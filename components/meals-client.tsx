"use client";

import { useRef } from "react";

import { MealFeed, MealFeedHandle } from "@/components/meal-feed";
import { MealForm } from "@/components/meal-form";

export function MealsClient() {
  const feedRef = useRef<MealFeedHandle>(null);

  return (
    <div className="space-y-10">
      <MealForm onLogged={() => feedRef.current?.refresh()} />
      <div>
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-faint">Recent meals</p>
        <div className="mt-3">
          <MealFeed ref={feedRef} />
        </div>
      </div>
    </div>
  );
}
