"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

import { authClient } from "@/lib/auth/client";

type AuthFormProps = {
  mode: "sign-in" | "sign-up";
  next?: string;
};

export function AuthForm({ mode, next }: AuthFormProps) {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const isSignUp = mode === "sign-up";

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);

    const form = new FormData(event.currentTarget);
    const email = String(form.get("email") ?? "").trim();
    const password = String(form.get("password") ?? "");
    const name = String(form.get("name") ?? "").trim();

    try {
      const result = isSignUp
        ? await authClient.signUp.email({ name, email, password })
        : await authClient.signIn.email({ email, password });

      if (result.error) {
        setError(result.error.message || "Authentication failed. Please try again.");
        return;
      }

      router.replace(next || (isSignUp ? "/onboarding" : "/dashboard"));
      router.refresh();
    } catch {
      setError("Authentication is temporarily unavailable. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form className="mt-8 space-y-5" onSubmit={handleSubmit}>
      {isSignUp ? (
        <label className="block text-sm font-semibold text-stone-700">
          Name
          <input
            autoComplete="name"
            className="mt-2 min-h-12 w-full rounded-2xl border border-stone-300 bg-white px-4 text-base outline-none transition focus:border-[#789416] focus:ring-4 focus:ring-[#d8ff62]/30"
            maxLength={80}
            name="name"
            required
          />
        </label>
      ) : null}

      <label className="block text-sm font-semibold text-stone-700">
        Email
        <input
          autoComplete="email"
          className="mt-2 min-h-12 w-full rounded-2xl border border-stone-300 bg-white px-4 text-base outline-none transition focus:border-[#789416] focus:ring-4 focus:ring-[#d8ff62]/30"
          name="email"
          required
          type="email"
        />
      </label>

      <label className="block text-sm font-semibold text-stone-700">
        Password
        <input
          autoComplete={isSignUp ? "new-password" : "current-password"}
          className="mt-2 min-h-12 w-full rounded-2xl border border-stone-300 bg-white px-4 text-base outline-none transition focus:border-[#789416] focus:ring-4 focus:ring-[#d8ff62]/30"
          minLength={8}
          name="password"
          required
          type="password"
        />
      </label>

      {error ? (
        <p aria-live="polite" className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800">
          {error}
        </p>
      ) : null}

      <button
        className="min-h-12 w-full rounded-2xl bg-[#15271e] px-5 py-3 text-sm font-bold text-white transition hover:bg-[#263c30] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#789416] disabled:cursor-wait disabled:opacity-60"
        disabled={isSubmitting}
        type="submit"
      >
        {isSubmitting ? "Please wait…" : isSignUp ? "Create account" : "Sign in"}
      </button>

      <p className="text-center text-sm text-stone-500">
        {isSignUp ? "Already have an account?" : "New to HYROX Coach?"}{" "}
        <Link
          className="font-semibold text-[#506b13] underline decoration-[#a4c72b] underline-offset-4"
          href={
            (isSignUp ? "/auth/sign-in" : "/auth/sign-up") +
            (next ? `?next=${encodeURIComponent(next)}` : "")
          }
        >
          {isSignUp ? "Sign in" : "Create one"}
        </Link>
      </p>
    </form>
  );
}
