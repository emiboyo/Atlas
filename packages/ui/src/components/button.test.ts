import { describe, expect, it } from "vitest";
import { buttonVariants } from "./button";

describe("buttonVariants", () => {
  it("applies the requested semantic variant and size", () => {
    const classes = buttonVariants({ variant: "outline", size: "lg" });

    expect(classes).toContain("border");
    expect(classes).toContain("h-12");
    expect(classes).not.toContain("bg-primary");
  });

  it("preserves caller classes", () => {
    expect(buttonVariants({ className: "w-full" })).toContain("w-full");
  });
});
