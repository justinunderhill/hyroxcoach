import { HealthStatus } from "@/components/health-status";
import Link from "next/link";

const foundationItems = [
  "Neon Database linked",
  "Neon Auth enabled",
  "FastAPI service boundary",
  "Mobile-first Next.js shell",
];

export default function Home() {
  return (
    <main className="min-h-screen px-5 py-6 sm:px-8 sm:py-10">
      <div className="mx-auto flex min-h-[calc(100vh-3rem)] max-w-6xl flex-col overflow-hidden rounded-[2rem] border border-white/70 bg-white shadow-[0_30px_90px_rgba(26,44,34,0.13)] sm:min-h-[calc(100vh-5rem)]">
        <header className="flex items-center justify-between border-b border-stone-200/80 px-6 py-5 sm:px-10">
          <div className="flex items-center gap-3">
            <span className="grid size-10 place-items-center rounded-2xl bg-[#15271e] text-sm font-black tracking-tight text-[#d8ff62]">
              HC
            </span>
            <div>
              <p className="text-sm font-bold tracking-[-0.02em] text-stone-900">HYROX Coach</p>
              <p className="text-xs text-stone-500">Doubles preparation</p>
            </div>
          </div>
          <Link className="min-h-10 rounded-full border border-[#cde95b] bg-[#f3ffd1] px-4 py-2 text-xs font-semibold text-[#38500e]" href="/auth/sign-in">
            Sign in
          </Link>
        </header>

        <section className="grid flex-1 lg:grid-cols-[1.3fr_0.7fr]">
          <div className="flex flex-col justify-center px-6 py-12 sm:px-10 sm:py-16 lg:px-16">
            <p className="mb-4 font-mono text-xs font-semibold uppercase tracking-[0.2em] text-[#567118]">
              Built for the shared mission
            </p>
            <h1 className="max-w-3xl text-balance text-4xl font-semibold leading-[1.04] tracking-[-0.055em] text-[#15221b] sm:text-6xl">
              Train individually. Arrive ready together.
            </h1>
            <p className="mt-6 max-w-2xl text-pretty text-base leading-7 text-stone-600 sm:text-lg">
              Secure athlete accounts and onboarding are ready. Training data will only appear once
              real athletes log it.
            </p>

            <div className="mt-8 flex flex-wrap gap-3">
              <Link className="inline-flex min-h-12 items-center rounded-2xl bg-[#15271e] px-5 text-sm font-bold text-white" href="/auth/sign-up">Create athlete account</Link>
              <Link className="inline-flex min-h-12 items-center rounded-2xl border border-stone-300 px-5 text-sm font-bold text-stone-700" href="/auth/sign-in">Sign in</Link>
            </div>

            <div className="mt-8 grid gap-3 sm:grid-cols-2">
              {foundationItems.map((item) => (
                <div
                  className="flex items-center gap-3 rounded-2xl border border-stone-200 bg-[#fafaf7] px-4 py-3 text-sm font-medium text-stone-700"
                  key={item}
                >
                  <span aria-hidden="true" className="size-2 rounded-full bg-[#a4c72b]" />
                  {item}
                </div>
              ))}
            </div>
          </div>

          <aside className="relative flex flex-col justify-between overflow-hidden bg-[#15271e] px-6 py-10 text-white sm:px-10 lg:px-12 lg:py-14">
            <div aria-hidden="true" className="absolute -right-20 -top-16 size-64 rounded-full border border-white/10" />
            <div aria-hidden="true" className="absolute -right-8 -top-4 size-36 rounded-full border border-[#d8ff62]/20" />

            <div className="relative">
              <p className="font-mono text-xs font-semibold uppercase tracking-[0.2em] text-[#d8ff62]">
                System check
              </p>
              <h2 className="mt-3 text-2xl font-semibold tracking-[-0.035em]">Frontend ↔ API</h2>
              <p className="mt-3 text-sm leading-6 text-white/65">
                This live check confirms that the browser can reach the FastAPI boundary.
              </p>
            </div>

            <div className="relative mt-10">
              <HealthStatus />
              <p className="mt-5 text-xs leading-5 text-white/45">
                No personal, workout, nutrition, or measurement data is created by this check.
              </p>
            </div>
          </aside>
        </section>
      </div>
    </main>
  );
}
