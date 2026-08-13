import Link from "next/link";

import { AuthForm } from "@/components/auth-form";

export default async function SignInPage({
  searchParams,
}: {
  searchParams: Promise<{ next?: string }>;
}) {
  const { next } = await searchParams;
  return (
    <main className="grid min-h-screen place-items-center px-5 py-10">
      <section className="w-full max-w-md rounded-[2rem] border border-line bg-surface p-7 shadow-[0_30px_90px_rgba(26,44,34,0.13)] sm:p-10">
        <Link className="text-sm font-bold text-lime" href="/">
          ← HYROX Coach
        </Link>
        <h1 className="mt-8 text-3xl font-semibold tracking-[-0.045em] text-ink">Welcome back</h1>
        <p className="mt-2 text-sm leading-6 text-muted">Sign in to continue your shared race preparation.</p>
        <AuthForm mode="sign-in" next={next} />
      </section>
    </main>
  );
}
