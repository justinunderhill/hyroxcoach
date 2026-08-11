import Link from "next/link";

import { AuthForm } from "@/components/auth-form";

export default function SignUpPage() {
  return (
    <main className="grid min-h-screen place-items-center px-5 py-10">
      <section className="w-full max-w-md rounded-[2rem] border border-white/70 bg-white p-7 shadow-[0_30px_90px_rgba(26,44,34,0.13)] sm:p-10">
        <Link className="text-sm font-bold text-[#506b13]" href="/">
          ← HYROX Coach
        </Link>
        <h1 className="mt-8 text-3xl font-semibold tracking-[-0.045em] text-[#15221b]">Create your account</h1>
        <p className="mt-2 text-sm leading-6 text-stone-500">Your records remain yours, even when you train as a team.</p>
        <AuthForm mode="sign-up" />
      </section>
    </main>
  );
}
