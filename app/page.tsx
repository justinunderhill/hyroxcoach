import Image from "next/image";
import Link from "next/link";

const featureItems = [
  "Race countdown that gives every session context",
  "Deterministic analytics — no invented readiness scores",
  "Shared team visibility without losing individual ownership",
  "AI coaching grounded in what you actually logged",
];

export default function Home() {
  return (
    <main className="min-h-screen px-5 py-6 sm:px-8 sm:py-10">
      <div className="mx-auto flex min-h-[calc(100vh-3rem)] max-w-6xl flex-col overflow-hidden rounded-[2rem] border border-line bg-surface shadow-[0_30px_90px_rgba(0,0,0,0.45)] sm:min-h-[calc(100vh-5rem)]">
        <header className="flex items-center justify-between border-b border-line px-6 py-5 sm:px-10">
          <Image alt="HYROX Coach" height={44} priority src="/logo.png" width={170} className="h-11 w-auto" />
          <Link
            className="min-h-10 rounded-full border border-lime/30 bg-lime/10 px-4 py-2 text-xs font-semibold text-lime"
            href="/auth/sign-in"
          >
            Sign in
          </Link>
        </header>

        <section className="grid flex-1 lg:grid-cols-[1.3fr_0.7fr]">
          <div className="flex flex-col justify-center px-6 py-12 sm:px-10 sm:py-16 lg:px-16">
            <p className="mb-4 font-mono text-xs font-semibold uppercase tracking-[0.2em] text-lime">
              Competitive athlete intelligence
            </p>
            <h1 className="max-w-3xl text-balance text-4xl font-semibold leading-[1.04] tracking-[-0.055em] text-ink sm:text-6xl">
              Train individually.{" "}
              <span className="text-lime">Arrive ready together.</span>
            </h1>
            <p className="mt-6 max-w-2xl text-pretty text-base leading-7 text-muted sm:text-lg">
              HYROX Coach tracks two athletes preparing for one race — running, stations, strength
              and recovery — and turns it into a shared read on whether you&apos;re actually ready.
            </p>

            <div className="mt-8 flex flex-wrap gap-3">
              <Link
                className="inline-flex min-h-12 items-center rounded-2xl bg-lime px-5 text-sm font-bold text-lime-ink"
                href="/auth/sign-up"
              >
                Create athlete account
              </Link>
              <Link
                className="inline-flex min-h-12 items-center rounded-2xl border border-line-strong px-5 text-sm font-bold text-ink"
                href="/auth/sign-in"
              >
                Sign in
              </Link>
            </div>

            <div className="mt-10 grid gap-3 sm:grid-cols-2">
              {featureItems.map((item) => (
                <div
                  className="flex items-center gap-3 rounded-2xl border border-line bg-surface-2 px-4 py-3 text-sm font-medium text-muted"
                  key={item}
                >
                  <span aria-hidden="true" className="size-2 shrink-0 rounded-full bg-lime" />
                  {item}
                </div>
              ))}
            </div>
          </div>

          <aside className="relative flex flex-col justify-center overflow-hidden bg-canvas px-6 py-10 sm:px-10 lg:px-12 lg:py-14">
            <div aria-hidden="true" className="absolute -right-20 -top-16 size-64 rounded-full border border-line" />
            <div aria-hidden="true" className="absolute -right-8 -top-4 size-36 rounded-full border border-lime/20" />

            <div className="relative rounded-3xl border border-line bg-surface p-6">
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-faint">Johannesburg HYROX</p>
              <p className="mt-2 font-mono text-4xl font-bold tabular-nums text-lime">108</p>
              <p className="text-xs text-muted">days to race</p>

              <div className="mt-6 grid grid-cols-3 gap-3 border-t border-line pt-5">
                <div>
                  <p className="text-lg font-semibold tabular-nums text-ink">4</p>
                  <p className="text-[11px] text-faint">sessions</p>
                </div>
                <div>
                  <p className="text-lg font-semibold tabular-nums text-ink">18.2</p>
                  <p className="text-[11px] text-faint">km running</p>
                </div>
                <div>
                  <p className="text-lg font-semibold tabular-nums text-ink">7/10</p>
                  <p className="text-[11px] text-faint">coverage</p>
                </div>
              </div>
            </div>

            <p className="relative mt-5 text-xs leading-5 text-faint">
              An illustrative preview — your dashboard is built entirely from what you log.
            </p>
          </aside>
        </section>
      </div>
    </main>
  );
}
