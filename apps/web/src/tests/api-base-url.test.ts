import { afterEach, describe, expect, test, vi } from "vitest";

import { getApiBaseUrl } from "../lib/api-client";

/** Where the browser sends uploads (DEC-097). */
describe("the preparation service's address", () => {
    afterEach(() => vi.unstubAllEnvs());

    test("a configured address always wins", () => {
        vi.stubEnv("NEXT_PUBLIC_EXAM_PHOTO_API_BASE_URL", "http://192.168.29.72:8000");
        vi.stubEnv("NODE_ENV", "production");
        expect(getApiBaseUrl()).toBe("http://192.168.29.72:8000");
    });

    test("deployed with no address, uploads go to the page's own origin, never to the phone itself", () => {
        vi.stubEnv("NEXT_PUBLIC_EXAM_PHOTO_API_BASE_URL", "");
        vi.stubEnv("NODE_ENV", "production");
        expect(getApiBaseUrl()).toBe(window.location.origin);
        expect(getApiBaseUrl()).not.toContain("127.0.0.1");
        expect(new URL("/v1/exams", getApiBaseUrl()).pathname).toBe("/v1/exams");
    });

    test("local development with no address keeps the engine's port", () => {
        vi.stubEnv("NEXT_PUBLIC_EXAM_PHOTO_API_BASE_URL", "");
        vi.stubEnv("NODE_ENV", "development");
        expect(getApiBaseUrl()).toBe("http://127.0.0.1:8000");
    });
});
