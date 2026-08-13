"use client";

import { useEffect, useState } from "react";

import { authenticatedFetch } from "@/lib/auth/client";
import {
  createTeamInvite,
  getTeam,
  listTeamInvites,
  Team,
  TeamInvite,
} from "@/lib/team";

type State =
  | { status: "loading" }
  | { status: "no-team" }
  | { status: "ready"; teamId: string; team: Team; invites: TeamInvite[] }
  | { status: "error"; message: string };

function pendingInvite(invites: TeamInvite[]): TeamInvite | undefined {
  const now = Date.now();
  return invites.find(
    (invite) => invite.accepted_at === null && new Date(invite.expires_at).getTime() > now,
  );
}

export function TeamInviteCard() {
  const [state, setState] = useState<State>({ status: "loading" });
  const [isCreating, setIsCreating] = useState(false);
  const [freshLink, setFreshLink] = useState<string | null>(null);
  const [copyLabel, setCopyLabel] = useState("Copy link");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    void authenticatedFetch("/api/me", { signal: controller.signal })
      .then(async (response) => {
        if (!response.ok) throw new Error();
        const me = await response.json();
        const teamId: string | undefined = me.active_teams?.[0]?.id;
        if (!teamId) {
          setState({ status: "no-team" });
          return;
        }
        const [team, invites] = await Promise.all([
          getTeam(teamId, controller.signal),
          listTeamInvites(teamId, controller.signal),
        ]);
        setState({ status: "ready", teamId, team, invites });
      })
      .catch((fetchError: unknown) => {
        if (fetchError instanceof DOMException && fetchError.name === "AbortError") return;
        setState({ status: "error", message: "Your team could not be loaded." });
      });
    return () => controller.abort();
  }, []);

  async function handleInvite() {
    if (state.status !== "ready") return;
    setError(null);
    setIsCreating(true);
    try {
      const created = await createTeamInvite(state.teamId);
      const link = `${window.location.origin}/join/${created.token}`;
      setFreshLink(link);
      const invites = await listTeamInvites(state.teamId);
      setState({ ...state, invites });
    } catch (inviteError) {
      setError(
        inviteError instanceof Error ? inviteError.message : "The invite could not be created.",
      );
    } finally {
      setIsCreating(false);
    }
  }

  async function handleCopy() {
    if (!freshLink) return;
    try {
      await navigator.clipboard.writeText(freshLink);
      setCopyLabel("Copied!");
      setTimeout(() => setCopyLabel("Copy link"), 2000);
    } catch {
      // Clipboard access can be denied; the link is still shown for manual copy.
    }
  }

  if (state.status === "loading" || state.status === "no-team") return null;
  if (state.status === "error") {
    return <p className="rounded-3xl bg-rose-50 p-6 text-sm text-rose-800">{state.message}</p>;
  }

  const { team, invites } = state;
  const pending = pendingInvite(invites);
  const hasPartner = team.members.length >= 2;

  return (
    <div className="rounded-3xl border border-stone-200 bg-white p-6">
      <p className="text-xs font-semibold uppercase tracking-[0.18em] text-stone-400">Team</p>
      <h3 className="mt-2 text-sm font-semibold text-[#15221b]">{team.name}</h3>
      <ul className="mt-3 space-y-1 text-sm text-stone-600">
        {team.members.map((member) => (
          <li key={member.user_id}>
            {member.display_name}
            {member.role === "owner" ? " (owner)" : ""}
          </li>
        ))}
      </ul>

      {hasPartner ? (
        <p className="mt-4 text-xs text-stone-400">Your team is complete.</p>
      ) : (
        <div className="mt-4">
          {freshLink ? (
            <div className="rounded-2xl bg-[#f8ffe4] p-4">
              <p className="text-xs font-semibold text-[#38500e]">
                Share this link with your partner — it&apos;s only shown once.
              </p>
              <p className="mt-2 break-all rounded-xl bg-white px-3 py-2 text-xs text-stone-600">
                {freshLink}
              </p>
              <button
                className="mt-3 min-h-9 rounded-xl border border-[#263711]/20 px-3 text-xs font-semibold text-[#263711]"
                onClick={handleCopy}
                type="button"
              >
                {copyLabel}
              </button>
            </div>
          ) : pending ? (
            <p className="text-xs text-stone-500">
              Invite pending, expires{" "}
              {new Date(pending.expires_at).toLocaleDateString()}. Generate a new one if the link
              was lost.
            </p>
          ) : null}

          {error ? <p className="mt-2 text-xs text-rose-700">{error}</p> : null}

          <button
            className="mt-3 min-h-10 rounded-xl bg-[#15271e] px-4 text-xs font-bold text-white disabled:opacity-60"
            disabled={isCreating}
            onClick={handleInvite}
            type="button"
          >
            {isCreating ? "Creating…" : pending ? "Generate new invite link" : "Invite partner"}
          </button>
        </div>
      )}
    </div>
  );
}
