import { authenticatedFetch } from "@/lib/auth/client";

export type TeamMember = {
  user_id: string;
  display_name: string;
  role: "owner" | "athlete";
  status: string;
};

export type Team = {
  id: string;
  name: string;
  created_by: string;
  created_at: string;
  members: TeamMember[];
};

export type TeamInvite = {
  id: string;
  team_id: string;
  invited_email: string | null;
  expires_at: string;
  accepted_at: string | null;
  created_by: string;
  created_at: string;
};

export type TeamInviteCreateResult = TeamInvite & { token: string };

export type TeamInviteAcceptResult = {
  team_id: string;
  team_name: string;
  role: string;
  status: string;
};

async function errorMessage(response: Response, fallback: string): Promise<string> {
  const body = await response.json().catch(() => null);
  const message = body?.error?.message;
  return typeof message === "string" ? message : fallback;
}

export async function getTeam(teamId: string, signal?: AbortSignal): Promise<Team> {
  const response = await authenticatedFetch(`/api/teams/${teamId}`, { signal });
  if (!response.ok) {
    throw new Error(await errorMessage(response, "The team could not be loaded."));
  }
  return response.json();
}

export async function listTeamInvites(teamId: string, signal?: AbortSignal): Promise<TeamInvite[]> {
  const response = await authenticatedFetch(`/api/teams/${teamId}/invites`, { signal });
  if (!response.ok) {
    throw new Error(await errorMessage(response, "Invites could not be loaded."));
  }
  return response.json();
}

export async function createTeamInvite(
  teamId: string,
  invitedEmail?: string | null,
): Promise<TeamInviteCreateResult> {
  const response = await authenticatedFetch(`/api/teams/${teamId}/invites`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ invited_email: invitedEmail || null }),
  });
  if (!response.ok) {
    throw new Error(await errorMessage(response, "The invite could not be created."));
  }
  return response.json();
}

export async function acceptTeamInvite(token: string): Promise<TeamInviteAcceptResult> {
  const response = await authenticatedFetch(`/api/team-invites/${token}/accept`, {
    method: "POST",
  });
  if (!response.ok) {
    throw new Error(await errorMessage(response, "This invite could not be accepted."));
  }
  return response.json();
}
