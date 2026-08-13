"use client";

import Link from "next/link";
import { useState } from "react";

const QUICK_LOG_ITEMS: { emoji: string; label: string; href: string }[] = [
  { emoji: "🏃", label: "Run", href: "/workouts" },
  { emoji: "🏋", label: "Strength", href: "/workouts" },
  { emoji: "🥊", label: "MMA", href: "/workouts" },
  { emoji: "🚶", label: "Walk", href: "/workouts" },
  { emoji: "🔥", label: "HYROX", href: "/workouts" },
  { emoji: "🧘", label: "Recovery", href: "/workouts" },
  { emoji: "🍽", label: "Meal", href: "/meals" },
  { emoji: "📷", label: "Upload", href: "/workouts" },
];

export function BottomNav() {
  const [open, setOpen] = useState(false);

  return (
    <>
      {open ? (
        <div className="fixed inset-0 z-40 flex items-end bg-black/60" onClick={() => setOpen(false)}>
          <div
            className="w-full rounded-t-[2rem] border-t border-line bg-surface p-6 pb-8"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="mx-auto mb-4 h-1 w-10 rounded-full bg-line-strong" />
            <p className="text-sm font-semibold text-ink">What did you do?</p>
            <div className="mt-4 grid grid-cols-4 gap-3">
              {QUICK_LOG_ITEMS.map((item) => (
                <Link
                  className="flex flex-col items-center gap-1.5 rounded-2xl border border-line bg-surface-2 py-4 text-center"
                  href={item.href}
                  key={item.label}
                  onClick={() => setOpen(false)}
                >
                  <span aria-hidden="true" className="text-2xl">{item.emoji}</span>
                  <span className="text-[11px] font-semibold text-muted">{item.label}</span>
                </Link>
              ))}
            </div>
            <p className="mt-4 text-center text-xs font-semibold uppercase tracking-[0.14em] text-faint">
              Quick workouts
            </p>
            <Link
              className="mt-2 flex min-h-11 items-center justify-center rounded-xl border border-lime/30 bg-lime/10 text-sm font-bold text-lime"
              href="/cindy"
              onClick={() => setOpen(false)}
            >
              Cindy
            </Link>
          </div>
        </div>
      ) : null}

      <nav className="fixed inset-x-0 bottom-0 z-30 border-t border-line bg-surface/95 backdrop-blur">
        <div className="mx-auto flex max-w-lg items-center justify-between px-6 py-2 sm:px-10">
          <Link className="flex flex-col items-center gap-1 px-2 py-1 text-[11px] font-semibold text-muted" href="/dashboard">
            <span aria-hidden="true" className="text-lg">🏠</span>
            Home
          </Link>
          <Link className="flex flex-col items-center gap-1 px-2 py-1 text-[11px] font-semibold text-muted" href="/dashboard#progress">
            <span aria-hidden="true" className="text-lg">📈</span>
            Progress
          </Link>
          <button
            aria-label="Log activity"
            className="-mt-6 grid size-14 shrink-0 place-items-center rounded-full bg-lime text-2xl font-black text-lime-ink shadow-[0_8px_24px_rgba(200,255,61,0.4)]"
            onClick={() => setOpen(true)}
            type="button"
          >
            +
          </button>
          <Link className="flex flex-col items-center gap-1 px-2 py-1 text-[11px] font-semibold text-muted" href="/dashboard#team">
            <span aria-hidden="true" className="text-lg">🤝</span>
            Team
          </Link>
          <Link className="flex flex-col items-center gap-1 px-2 py-1 text-[11px] font-semibold text-muted" href="/dashboard#coach">
            <span aria-hidden="true" className="text-lg">🧠</span>
            Coach
          </Link>
        </div>
      </nav>
    </>
  );
}
