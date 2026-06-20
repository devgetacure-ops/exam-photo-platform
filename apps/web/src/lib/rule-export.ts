/**
 * Triggers a browser download of the rule JSON document.
 */
export function exportRuleJson(rule: object, filename: string): void {
  const jsonStr = JSON.stringify(rule, null, 2);
  const blob = new Blob([jsonStr], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  
  const link = document.createElement("a");
  link.href = url;
  link.download = filename.endsWith(".json") ? filename : `${filename}.json`;
  document.body.appendChild(link);
  link.click();
  
  // Clean up references immediately
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}
