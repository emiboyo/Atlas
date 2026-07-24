import { render, screen } from "@testing-library/react";
import HomePage from "../app/page";

describe("HomePage", () => {
  it("presents the Atlas AI positioning", () => {
    render(<HomePage />);
    expect(
      screen.getByRole("heading", { name: /the intelligent investment operating system/i }),
    ).toBeInTheDocument();
  });
});
