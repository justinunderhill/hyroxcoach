"use client";

import { useRef } from "react";

import { WorkoutFeed, WorkoutFeedHandle } from "@/components/workout-feed";
import { WorkoutForm } from "@/components/workout-form";

export function WorkoutsClient() {
  const feedRef = useRef<WorkoutFeedHandle>(null);

  return (
    <div className="space-y-10">
      <WorkoutForm onLogged={() => feedRef.current?.refresh()} />
      <div>
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-faint">Recent activity</p>
        <div className="mt-3">
          <WorkoutFeed ref={feedRef} />
        </div>
      </div>
    </div>
  );
}
