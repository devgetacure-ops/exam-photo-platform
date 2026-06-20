import { RuleDocument } from "./types";

export interface RuleSampleMetadata {
  id: string;
  label: string;
  path: string;
}

export const RULE_SAMPLES: RuleSampleMetadata[] = [
  {
    id: "exact_300x400",
    label: "Fictional Exact 300x400 White BG Exam",
    path: "/rules/sample_exact_300x400_50kb_white_bg.json",
  },
  {
    id: "range_200_300",
    label: "Fictional Range Dimensions White BG Exam",
    path: "/rules/sample_range_200_300_width_230_400_height_50kb_white_bg.json",
  },
];

/**
 * Fetches the full JSON rule from the public static assets directory.
 */
export async function fetchSampleRule(sample: RuleSampleMetadata): Promise<RuleDocument> {
  const response = await fetch(sample.path);
  if (!response.ok) {
    throw new Error(`Failed to load sample rule: ${response.statusText}`);
  }
  return await response.json();
}
