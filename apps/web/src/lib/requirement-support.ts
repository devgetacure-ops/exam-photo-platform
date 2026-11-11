import type { RequirementSummary } from "./types";

/** A requirement the platform prepares a file for (DEC-056: never a boolean elsewhere). */
export function isOurs(requirement: RequirementSummary): boolean {
    return (
        requirement.platform_support === "supported" ||
        requirement.platform_support === "partially_supported"
    );
}
