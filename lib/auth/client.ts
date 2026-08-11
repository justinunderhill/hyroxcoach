"use client";

import { createAuthClient } from "@neondatabase/auth/next";

export const authClient = createAuthClient();

export async function getAccessToken(): Promise<string | null> {
  const response = await fetch("/api/auth/token", {
    headers: { Accept: "application/json" },
  });

  if (response.status === 401) {
    return null;
  }
  if (!response.ok) {
    throw new Error("Unable to create an API access token.");
  }

  const payload: unknown = await response.json();
  if (
    typeof payload !== "object" ||
    payload === null ||
    !("token" in payload) ||
    typeof payload.token !== "string"
  ) {
    throw new Error("Neon Auth returned an invalid access token response.");
  }

  return payload.token;
}

export async function authenticatedFetch(input: RequestInfo | URL, init: RequestInit = {}) {
  const token = await getAccessToken();
  if (!token) {
    throw new Error("Your session has expired. Please sign in again.");
  }

  const headers = new Headers(init.headers);
  headers.set("Authorization", `Bearer ${token}`);
  headers.set("Accept", "application/json");

  return fetch(input, { ...init, headers });
}
