"use client";

import { useEffect } from "react";

export function ServiceWorkerRegister() {
  useEffect(() => {
    if (!("serviceWorker" in navigator)) return;
    navigator.serviceWorker.register("/sw.js").catch(() => {
      // Installability/offline fallback is a progressive enhancement; a failed
      // registration should never block the app from working online.
    });
  }, []);

  return null;
}
