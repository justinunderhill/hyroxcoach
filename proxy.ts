import type { NextRequest } from "next/server";

import { getServerAuth } from "@/lib/auth/server";

export default function proxy(request: NextRequest) {
  return getServerAuth().middleware({ loginUrl: "/auth/sign-in" })(request);
}

export const config = {
  matcher: ["/dashboard/:path*", "/onboarding/:path*"],
};
