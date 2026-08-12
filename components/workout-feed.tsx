"use client";

import { forwardRef, useEffect, useImperativeHandle, useState } from "react";

import { WorkoutInsightButton } from "@/components/workout-insight-button";
import { authenticatedFetch } from "@/lib/auth/client";
import { listMedia, MediaItem } from "@/lib/media";

type Workout = {
  id: string;
  user_id: string;
  occurred_at: string;
  title: string;
  activity_type: string;
  category_slugs: string[];
  duration_minutes: number | null;
  distance_km: string | null;
  rpe: number | null;
  visibility: "team" | "private";
};

type FeedState =
  | { status: "loading" }
  | { status: "ready"; workouts: Workout[]; mediaByWorkoutId: Map<string, MediaItem[]> }
  | { status: "error" };

export type WorkoutFeedHandle = {
  refresh: () => void;
};

function formatMeta(workout: Workout): string {
  const parts: string[] = [];
  if (workout.distance_km) parts.push(`${Number(workout.distance_km).toFixed(2)} km`);
  if (workout.duration_minutes) parts.push(`${workout.duration_minutes} min`);
  if (workout.rpe) parts.push(`RPE ${workout.rpe}`);
  return parts.join(" · ");
}

export const WorkoutFeed = forwardRef<WorkoutFeedHandle>(function WorkoutFeed(_props, ref) {
  const [state, setState] = useState<FeedState>({ status: "loading" });
  const [reloadToken, setReloadToken] = useState(0);

  useImperativeHandle(ref, () => ({
    refresh: () => setReloadToken((token) => token + 1),
  }));

  useEffect(() => {
    const controller = new AbortController();
    setState({ status: "loading" });
    void authenticatedFetch("/api/workouts?limit=20", { signal: controller.signal })
      .then(async (response) => {
        if (!response.ok) throw new Error();
        const workouts: Workout[] = await response.json();
        const media = await listMedia(
          "workout",
          workouts.map((workout) => workout.id),
          controller.signal,
        ).catch(() => []);
        const mediaByWorkoutId = new Map<string, MediaItem[]>();
        for (const item of media) {
          const existing = mediaByWorkoutId.get(item.entity_id) ?? [];
          existing.push(item);
          mediaByWorkoutId.set(item.entity_id, existing);
        }
        setState({ status: "ready", workouts, mediaByWorkoutId });
      })
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setState({ status: "error" });
      });
    return () => controller.abort();
  }, [reloadToken]);

  if (state.status === "loading") return <div className="h-40 animate-pulse rounded-3xl bg-stone-100" />;
  if (state.status === "error") {
    return <p className="rounded-3xl bg-rose-50 p-6 text-sm text-rose-800">Recent activity could not be loaded.</p>;
  }
  if (state.workouts.length === 0) {
    return (
      <div className="rounded-3xl border border-dashed border-stone-300 bg-white/50 p-6">
        <p className="text-sm text-stone-500">No workouts logged yet. Log your first session above.</p>
      </div>
    );
  }

  return (
    <ul className="space-y-3">
      {state.workouts.map((workout) => (
        <li className="rounded-2xl border border-stone-200 bg-white p-4" key={workout.id}>
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="font-semibold text-[#15221b]">{workout.title}</p>
              <p className="mt-0.5 text-xs text-stone-500">
                {new Date(workout.occurred_at).toLocaleString(undefined, {
                  dateStyle: "medium",
                  timeStyle: "short",
                })}
              </p>
            </div>
            <span className="shrink-0 rounded-full bg-[#f8ffe4] px-2.5 py-1 text-xs font-semibold text-[#567118]">
              {workout.visibility === "team" ? "Team" : "Private"}
            </span>
          </div>
          {formatMeta(workout) ? <p className="mt-2 text-sm text-stone-600">{formatMeta(workout)}</p> : null}
          {workout.category_slugs.length > 0 ? (
            <p className="mt-2 text-xs uppercase tracking-[0.1em] text-stone-400">
              {workout.category_slugs.join(", ")}
            </p>
          ) : null}
          {(state.mediaByWorkoutId.get(workout.id) ?? []).length > 0 ? (
            <div className="mt-3 flex gap-2">
              {(state.mediaByWorkoutId.get(workout.id) ?? []).map((item) => (
                <a href={item.view_url} key={item.media_asset.id} rel="noreferrer" target="_blank">
                  <img
                    alt="Workout evidence"
                    className="size-16 rounded-xl border border-stone-200 object-cover"
                    src={item.view_url}
                  />
                </a>
              ))}
            </div>
          ) : null}
          <WorkoutInsightButton workoutId={workout.id} />
        </li>
      ))}
    </ul>
  );
});
