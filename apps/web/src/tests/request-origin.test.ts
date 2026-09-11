import { describe, expect, test } from "vitest";
import { isSameOrigin } from "../lib/request-origin";

const headers = (values: Record<string, string>) => new Headers(values);

describe("request origin check", () => {
    test("a page on the host the browser addressed is accepted", () => {
        expect(
            isSameOrigin(
                headers({ origin: "http://127.0.0.1:3007", host: "127.0.0.1:3007" }),
            ),
        ).toBe(true);
    });

    test("behind a proxy the forwarded host is the one the candidate typed", () => {
        expect(
            isSameOrigin(
                headers({
                    origin: "https://examuploadkit.in",
                    host: "10.0.0.4:3000",
                    "x-forwarded-host": "examuploadkit.in",
                }),
            ),
        ).toBe(true);
    });

    test("the configured site URL is accepted", () => {
        expect(
            isSameOrigin(
                headers({ origin: "https://examuploadkit.in", host: "internal:3000" }),
                "https://examuploadkit.in",
            ),
        ).toBe(true);
    });

    test("a post from another site is refused", () => {
        expect(
            isSameOrigin(
                headers({ origin: "https://elsewhere.example", host: "examuploadkit.in" }),
            ),
        ).toBe(false);
    });

    test("no origin, or a malformed one, is refused", () => {
        expect(isSameOrigin(headers({ host: "examuploadkit.in" }))).toBe(false);
        expect(
            isSameOrigin(headers({ origin: "not a url", host: "examuploadkit.in" })),
        ).toBe(false);
    });
});
