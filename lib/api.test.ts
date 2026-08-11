import { afterEach, describe, expect, it, vi } from "vitest";

import { getApiHealth } from "./api";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("getApiHealth", () => {
  it("returns a validated health response", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify({ status: "ok", service: "hyrox-coach-api" }), {
          status: 200,
        }),
      ),
    );

    await expect(getApiHealth()).resolves.toEqual({
      status: "ok",
      service: "hyrox-coach-api",
    });
  });

  it("rejects malformed responses", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response(JSON.stringify({ status: "ok" }), { status: 200 })),
    );

    await expect(getApiHealth()).rejects.toThrow("invalid health response");
  });
});
