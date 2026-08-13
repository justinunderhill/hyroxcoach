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
        <label className="block text-sm font-semibold text-ink">
          Name
          <input
            autoComplete="name"
            className="mt-2 min-h-12 w-full rounded-2xl border border-line-strong bg-surface px-4 text-base outline-none transition focus:border-lime focus:ring-4 focus:ring-lime/30"
            maxLength={80}
            name="name"
            required
          />
        </label>
      ) : null}

      <label className="block text-sm font-semibold text-ink">
        Email
        <input
          autoComplete="email"
          className="mt-2 min-h-12 w-full rounded-2xl border border-line-strong bg-surface px-4 text-base outline-none transition focus:border-lime focus:ring-4 focus:ring-lime/30"
          name="email"
          required
          type="email"
        />
      </label>

      <label className="block text-sm font-semibold text-ink">
        Password
        <input
          autoComplete={isSignUp ? "new-password" : "current-password"}
          className="mt-2 min-h-12 w-full rounded-2xl border border-line-strong bg-surface px-4 text-base outline-none transition focus:border-lime focus:ring-4 focus:ring-lime/30"
          minLength={8}
          name="password"
          required
          type="password"
        />
      </label>

      {error ? (
        <p aria-live="polite" className="rounded-2xl border border-red/30 bg-red/10 px-4 py-3 text-sm text-red">
          {error}
        </p>
      ) : null}

      <button
        className="min-h-12 w-full rounded-2xl bg-lime px-5 py-3 text-sm font-bold text-lime-ink transition hover:bg-lime/90 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-lime disabled:cursor-wait disabled:opacity-60"
        disabled={isSubmitting}
        type="submit"
      >
        {isSubmitting ? "Please wait…" : isSignUp ? "Create account" : "Sign in"}
      </button>

      <p className="text-center text-sm text-muted">
        {isSignUp ? "Already have an account?" : "New to HYROX Coach?"}{" "}
        <Link
          className="font-semibold text-lime underline decoration-lime underline-offset-4"
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
