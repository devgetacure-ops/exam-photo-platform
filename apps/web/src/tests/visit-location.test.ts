// @vitest-environment node
import { describe, expect, it } from "vitest";
import { locationFrom } from "../lib/visit-location";

describe("where a visitor is (DEC-125)", () => {
    it("reads Cloudflare's location headers", () => {
        const headers = new Headers({ "cf-ipcountry": "in", "cf-region": "Maharashtra", "cf-ipcity": "Pune" });
        expect(locationFrom(headers)).toEqual({ country: "IN", region: "Maharashtra", city: "Pune" });
    });

    it("decodes encoded city names", () => {
        expect(locationFrom(new Headers({ "cf-ipcity": "Bh%C3%A1galpur" })).city).toBe("Bhágalpur");
    });

    it("drops unknown and Tor countries and missing headers", () => {
        expect(locationFrom(new Headers({ "cf-ipcountry": "XX" }))).toEqual({});
        expect(locationFrom(new Headers({ "cf-ipcountry": "T1" }))).toEqual({});
        expect(locationFrom(new Headers())).toEqual({});
    });
});
