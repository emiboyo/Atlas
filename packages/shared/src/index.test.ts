import { describe, expect, it } from "vitest";
import { API_PREFIX } from "./index";

describe("shared API constants", () => {
  it("uses the versioned API prefix", () => {
    expect(API_PREFIX).toBe("/api/v1");
  });
});
