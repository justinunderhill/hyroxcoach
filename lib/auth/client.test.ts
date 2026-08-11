import { afterEach, describe, expect, it, vi } from "vitest";

vi.mock("@neondatabase/auth/next", () => ({
  createAuthClient: () => ({}),
}));

import { authenticatedFetch, getAccessToken } from "./client";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("Neon Auth API token handling", () => {
  it("reads a JWT from the same-origin token endpoint", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response(JSON.stringify({ token: "signed-token" }))),
    );

    await expect(getAccessToken()).resolves.toBe("signed-token");
  });

  it("adds the bearer token to FastAPI requests", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({ token: "signed-token" })))
      .mockResolvedValueOnce(new Response(null, { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);

    await authenticatedFetch("/api/me");

    const request = fetchMock.mock.calls[1];
    expect(request[0]).toBe("/api/me");
    expect((request[1]?.headers as Headers).get("Authorization")).toBe("Bearer signed-token");
  });
});
