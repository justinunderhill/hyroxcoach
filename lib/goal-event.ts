import { authenticatedFetch } from "@/lib/auth/client";

export type GoalEvent = {
  id: string;
  team_id: string;
  name: string;
  event_type: "hyrox_doubles";
  event_date: string;
  division: string | null;
  location: string | null;
  preparation_start_date: string | null;
  days_until_event: number;
  is_taper_week: boolean;
  created_at: string;
  updated_at: string;
};

export type GoalEventUpsert = {
  name: string;
  event_date: string;
  division?: string | null;
  location?: string | null;
  preparation_start_date?: string | null;
};

async function errorMessage(response: Response, fallback: string): Promise<string> {
  const body = await response.json().catch(() => null);
  const message = body?.error?.message;
  return typeof message === "string" ? message : fallback;
}

export async function getGoalEvent(
  teamId: string,
  signal?: AbortSignal,
): Promise<GoalEvent | null> {
  const response = await authenticatedFetch(`/api/teams/${teamId}/goal-event`, { signal });
  if (!response.ok) {
    throw new Error(await errorMessage(response, "The target event could not be loaded."));
  }
  return response.json();
}

export async function upsertGoalEvent(
  teamId: string,
  payload: GoalEventUpsert,
): Promise<GoalEvent> {
  const response = await authenticatedFetch(`/api/teams/${teamId}/goal-event`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw new Error(await errorMessage(response, "The target event could not be saved."));
  }
  return response.json();
}
