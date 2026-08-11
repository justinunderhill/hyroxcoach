"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { authenticatedFetch } from "@/lib/auth/client";

type Profile = {
  display_name: string;
  timezone: string;
  training_days: string[];
};

type ProfileState =
  | { status: "loading" }
  | { status: "empty" }
  | { status: "ready"; profile: Profile }
  | { status: "error" };

export function ProfileSummary() {
  const [state, setState] = useState<ProfileState>({ status: "loading" });

  useEffect(() => {
    const controller = new AbortController();
    void authenticatedFetch("/api/me", { signal: controller.signal })
      .then(async (response) => {
        if (!response.ok) throw new Error();
        const payload = await response.json();
        setState(payload.profile ? { status: "ready", profile: payload.profile } : { status: "empty" });
      })
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setState({ status: "error" });
      });
    return () => controller.abort();
  }, []);

  if (state.status === "loading") return <div className="h-32 animate-pulse rounded-3xl bg-stone-100" />;
  if (state.status === "empty") {
    return (
      <div className="rounded-3xl border border-[#dbe998] bg-[#f8ffe4] p-6">
        <h2 className="font-semibold text-[#263711]">Complete your athlete profile</h2>
        <p className="mt-2 text-sm text-stone-600">Add your timezone and training availability before creating a team.</p>
        <Link className="mt-5 inline-flex min-h-11 items-center rounded-xl bg-[#15271e] px-4 text-sm font-bold text-white" href="/onboarding">Finish onboarding</Link>
      </div>
    );
  }
  if (state.status === "error") return <p className="rounded-3xl bg-rose-50 p-6 text-sm text-rose-800">Your profile could not be loaded.</p>;

  return (
    <div className="rounded-3xl border border-stone-200 bg-white p-6">
      <p className="text-xs font-semibold uppercase tracking-[0.18em] text-stone-400">Athlete</p>
      <h2 className="mt-2 text-2xl font-semibold tracking-[-0.035em] text-[#15221b]">{state.profile.display_name}</h2>
      <p className="mt-1 text-sm text-stone-500">{state.profile.timezone}</p>
      <p className="mt-5 text-sm text-stone-600">{state.profile.training_days.length ? `Available ${state.profile.training_days.join(", ")}` : "Training availability not set yet."}</p>
    </div>
  );
}
