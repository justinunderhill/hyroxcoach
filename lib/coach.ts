import { authenticatedFetch } from "@/lib/auth/client";

export type CoachStatus = "on_track" | "mixed" | "needs_attention" | "insufficient_data";

export type CoachWin = { title: string; evidence: string };
export type CoachGap = { title: string; evidence: string; priority: "low" | "medium" | "high" };
export type CoachRecommendation = {
  action: string;
  reason: string;
  time_horizon: "next_session" | "this_week" | "next_2_weeks";
};

export type CoachInsightData = {
  summary: string;
  status: CoachStatus;
  wins: CoachWin[];
  gaps: CoachGap[];
  recommendations: CoachRecommendation[];
  team_notes: string[];
  data_limits: string[];
};

export type CoachInsightResponse = {
  id: string;
  scope: "workout" | "daily" | "weekly" | "team_weekly";
  user_id: string | null;
  team_id: string;
  period_start: string | null;
  period_end: string | null;
  source_record_id: string | null;
  coach_version: string;
  model_name: string;
  insight: CoachInsightData;
  created_at: string;
};

async function errorMessage(response: Response, fallback: string): Promise<string> {
  const body = await response.json().catch(() => null);
  const message = body?.error?.message;
  return typeof message === "string" ? message : fallback;
}

export async function getWeeklyReview(signal?: AbortSignal): Promise<CoachInsightResponse> {
  const response = await authenticatedFetch("/api/coach/weekly", { signal });
  if (!response.ok) {
    throw new Error(await errorMessage(response, "The weekly review could not be generated."));
  }
  return response.json();
}

export async function getTeamWeeklyReview(
  teamId: string,
  signal?: AbortSignal,
): Promise<CoachInsightResponse> {
  const response = await authenticatedFetch(`/api/coach/team/${teamId}/weekly`, { signal });
  if (!response.ok) {
    throw new Error(
      await errorMessage(response, "The team weekly review could not be generated."),
    );
  }
  return response.json();
}

export async function generateWorkoutInsight(workoutId: string): Promise<CoachInsightResponse> {
  const response = await authenticatedFetch(`/api/coach/workout/${workoutId}`, {
    method: "POST",
  });
  if (!response.ok) {
    throw new Error(await errorMessage(response, "The workout insight could not be generated."));
  }
  return response.json();
}
