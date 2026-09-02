import { describe, test, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { ExamSearch } from "../components/exam-search";
import type { SearchEntry } from "../lib/types";

const push = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push }),
}));

const exams: SearchEntry[] = [
  {
    id: "common-admission-test-2025",
    name: "Common Admission Test 2025",
    body: "Indian Institutes of Management",
    year: 2025,
    aliases: ["CAT 2025"],
    prepares: 4,
    total: 4,
  },
  {
    id: "gate-2026",
    name: "GATE 2026",
    body: "Indian Institute of Science",
    year: 2026,
    aliases: ["GATE"],
    prepares: 2,
    total: 3,
  },
  {
    id: "rbi-assistant-2025",
    name: "RBI Assistant - Panel Year 2025",
    body: "Reserve Bank of India",
    year: 2025,
    aliases: ["RBI Assistant"],
    prepares: 4,
    total: 5,
  },
];

const unavailable: SearchEntry[] = [
  {
    id: "",
    name: "SSC Combined Graduate Level Examination 2026",
    body: "",
    year: 0,
    aliases: [],
    prepares: 0,
    total: 0,
    unavailable: {
      reason: "live capture only",
      detail: "The portal photographs the candidate directly.",
      deliverables: 2,
    },
  },
];

function type(value: string) {
  fireEvent.change(screen.getByRole("combobox"), { target: { value } });
}

describe("exam picker search", () => {
  beforeEach(() => {
    push.mockClear();
  });

  test("shows nothing until the candidate types", () => {
    render(<ExamSearch exams={exams} unavailable={unavailable} />);
    expect(screen.queryByRole("listbox")).toBeNull();
  });

  test("an abbreviation finds the exam whose full name does not contain it", () => {
    render(<ExamSearch exams={exams} unavailable={unavailable} />);
    type("cat");
    expect(screen.getByText("Common Admission Test 2025")).toBeTruthy();
  });

  test("the full name works too", () => {
    render(<ExamSearch exams={exams} unavailable={unavailable} />);
    type("common admission");
    expect(screen.getByText("Common Admission Test 2025")).toBeTruthy();
  });

  test("search is case- and punctuation-insensitive", () => {
    render(<ExamSearch exams={exams} unavailable={unavailable} />);
    type("R.B.I.  ASSISTANT");
    expect(screen.getByText("RBI Assistant - Panel Year 2025")).toBeTruthy();
  });

  test("the conducting body is searchable", () => {
    render(<ExamSearch exams={exams} unavailable={unavailable} />);
    type("reserve bank");
    expect(screen.getByText("RBI Assistant - Panel Year 2025")).toBeTruthy();
  });

  test("an unencoded examination is shown, not hidden (DEC-056)", () => {
    render(<ExamSearch exams={exams} unavailable={unavailable} />);
    type("ssc");
    expect(
      screen.getByText("SSC Combined Graduate Level Examination 2026")
    ).toBeTruthy();
    expect(screen.getByText("Not yet available")).toBeTruthy();
  });

  test("an unencoded examination is not selectable and never routes", () => {
    render(<ExamSearch exams={exams} unavailable={unavailable} />);
    type("ssc");
    // Every selectable row is an option; the unavailable one must not be.
    const options = screen.queryAllByRole("option");
    expect(options).toHaveLength(0);
    fireEvent.keyDown(screen.getByRole("combobox"), { key: "Enter" });
    expect(push).not.toHaveBeenCalled();
  });

  test("it says what the candidate still loses to the gap", () => {
    render(<ExamSearch exams={exams} unavailable={unavailable} />);
    type("ssc");
    expect(screen.getByText(/other 2 uploads are on our list/i)).toBeTruthy();
  });

  test("selecting a result routes to that exam", () => {
    render(<ExamSearch exams={exams} unavailable={unavailable} />);
    type("gate");
    fireEvent.click(screen.getByText("GATE 2026"));
    expect(push).toHaveBeenCalledWith("/exam/gate-2026");
  });

  test("Enter selects the highlighted result", () => {
    render(<ExamSearch exams={exams} unavailable={unavailable} />);
    type("cat");
    fireEvent.keyDown(screen.getByRole("combobox"), { key: "Enter" });
    expect(push).toHaveBeenCalledWith("/exam/common-admission-test-2025");
  });

  test("no match explains coverage rather than showing an empty box", () => {
    render(<ExamSearch exams={exams} unavailable={unavailable} />);
    type("zzzz");
    expect(screen.getByText(/nothing matches/i)).toBeTruthy();
  });

  test("the row reports how many files we prepare, not how many exist", () => {
    render(<ExamSearch exams={exams} unavailable={unavailable} />);
    type("gate");
    // GATE has 3 requirements but we prepare 2 -- the promise is the smaller one.
    expect(screen.getByText("2 files")).toBeTruthy();
  });
});
