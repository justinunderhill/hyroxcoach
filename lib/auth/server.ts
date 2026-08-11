import { createNeonAuth } from "@neondatabase/auth/next/server";

const LOCAL_COOKIE_SECRET = "hyrox-coach-local-cookie-secret-not-for-production";

let authInstance: ReturnType<typeof createNeonAuth> | undefined;

function requiredEnvironmentValue(name: "NEON_AUTH_BASE_URL"): string {
  const value = process.env[name];
  if (!value) {
    throw new Error(`${name} is required.`);
  }
  return value;
}

function cookieSecret(): string {
  const configured = process.env.NEON_AUTH_COOKIE_SECRET;
  if (configured) {
    return configured;
  }

  if (process.env.NODE_ENV === "development" || process.env.NODE_ENV === "test") {
    return LOCAL_COOKIE_SECRET;
  }

  throw new Error("NEON_AUTH_COOKIE_SECRET is required outside local development.");
}

export function getServerAuth() {
  authInstance ??= createNeonAuth({
    baseUrl: requiredEnvironmentValue("NEON_AUTH_BASE_URL"),
    cookies: {
      secret: cookieSecret(),
    },
  });

  return authInstance;
}
