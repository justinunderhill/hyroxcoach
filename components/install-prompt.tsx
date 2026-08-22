"use client";

import { useEffect, useState } from "react";

const DISMISSED_KEY = "hyrox-coach-install-dismissed";

type BeforeInstallPromptEvent = Event & {
  prompt: () => Promise<void>;
  userChoice: Promise<{ outcome: "accepted" | "dismissed" }>;
};

export function InstallPrompt() {
  const [deferredPrompt, setDeferredPrompt] = useState<BeforeInstallPromptEvent | null>(null);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    if (localStorage.getItem(DISMISSED_KEY)) return;

    function handleBeforeInstallPrompt(event: Event) {
      event.preventDefault();
      setDeferredPrompt(event as BeforeInstallPromptEvent);
      setVisible(true);
    }

    window.addEventListener("beforeinstallprompt", handleBeforeInstallPrompt);
    return () => window.removeEventListener("beforeinstallprompt", handleBeforeInstallPrompt);
  }, []);

  function dismiss() {
    localStorage.setItem(DISMISSED_KEY, "1");
    setVisible(false);
  }

  async function install() {
    if (!deferredPrompt) return;
    await deferredPrompt.prompt();
    await deferredPrompt.userChoice;
    setDeferredPrompt(null);
    dismiss();
  }

  if (!visible || !deferredPrompt) return null;

  return (
    <div className="fixed inset-x-4 bottom-20 z-30 flex items-center gap-3 rounded-2xl border border-line bg-surface p-4 shadow-lg">
      <span aria-hidden="true" className="text-2xl">📲</span>
      <div className="flex-1">
        <p className="text-sm font-semibold text-ink">Add HYROX Coach to your home screen</p>
        <p className="text-xs text-muted">Faster access, full-screen, no browser bar.</p>
      </div>
      <button
        className="min-h-9 shrink-0 rounded-xl bg-lime px-3 text-xs font-bold text-lime-ink"
        onClick={install}
        type="button"
      >
        Add
      </button>
      <button
        aria-label="Dismiss"
        className="shrink-0 px-1 text-lg text-faint"
        onClick={dismiss}
        type="button"
      >
        ×
      </button>
    </div>
  );
}
