import type { NextConfig } from "next";
import { withSentryConfig } from "@sentry/nextjs";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  async rewrites() {
    if (process.env.NODE_ENV !== "development") {
      return [];
    }

    return [
      {
        source: "/api/:path((?!auth(?:/|$)).*)",
        destination: `${process.env.API_PROXY_TARGET ?? "http://127.0.0.1:8000"}/api/:path*`,
      },
    ];
  },
};

export default withSentryConfig(nextConfig, {
  org: process.env.SENTRY_ORG,
  project: process.env.SENTRY_PROJECT,
  silent: !process.env.CI,
  widenClientFileUpload: true,
});
