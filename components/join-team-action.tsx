"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { authenticatedFetch } from "@/lib/auth/client";
import { acceptTeamInvite } from "@/lib/team";

type State =
  | { status: "accepting" }
  | { status: "success"; teamName: string }
  | { status: "error"; message: string };

export function JoinTeamAction({ token }: { token: string }) {
  const router = useRouter();
  const [state, setState] = useState<State>({ status: "accepting" });

  useEffect(() => {
    let cancelled = false;
    void acceptTeamInvite(token)
      .then(async (result) => {
        if (cancelled) return;
        setState({ status: "success", teamName: result.team_name });
        const meResponse = await authenticatedFetch("/api/me");
        const me = meResponse.ok ? await meResponse.json() : null;
        setTimeout(() => {
          router.replace(me?.profile ? "/dashboard" : "/onboarding");
          router.refresh();
        }, 1500);
      })
      .catch((error: unknown) => {
        if (cancelled) return;
        setState({
          status: "error",
          message: error instanceof Error ? error.message : "This invite could not be accepted.",
        });
      });
    return () => {
      cancelled = true;
    };
  }, [token, router]);

  if (state.status === "accepting") {
    return <p className="mt-6 text-sm text-stone-500">Joining the team…</p>;
  }

  if (state.status === "success") {
    return (
      <p className="mt-6 rounded-2xl bg-[#f8ffe4] px-4 py-3 text-sm text-[#38500e]">
        You&apos;ve joined {state.teamName}. Taking you to your dashboard…
      </p>
    );
  }

  return (
    <p className="mt-6 rounded-2xl bg-rose-50 px-4 py-3 text-sm text-rose-800">{state.message}</p>
  );
}
