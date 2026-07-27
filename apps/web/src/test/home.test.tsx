import { render, screen } from "@testing-library/react";
import HomePage from "../app/page";

describe("HomePage", () => {
  it("presents the Atlas AI positioning", () => {
    render(<HomePage />);
    expect(
      screen.getByRole("heading", { name: /the intelligent investment operating system/i }),
    ).toBeInTheDocument();
  });

  it("only renders valid internal navigation targets", () => {
    const { container } = render(<HomePage />);
    const targets = Array.from(container.querySelectorAll("a")).map((link) =>
      link.getAttribute("href"),
    );

    expect(targets).not.toContain("#");
    expect(targets).toEqual(
      expect.arrayContaining(["/", "#features", "#architecture", "#roadmap"]),
    );
  });
});
