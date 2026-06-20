/**
 * Safely sets a value inside a nested object by dot path (e.g., "image_requirements.dimensions.width_px").
 * Handles intermediate object creation if necessary, preserving all other fields.
 */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export function setNestedValue(obj: any, path: string, value: any): any {
  if (obj === null || obj === undefined) {
    obj = {};
  }
  // Deep clone to ensure no mutating side-effects on original React state
  const newObj = JSON.parse(JSON.stringify(obj));
  const parts = path.split(".");
  let current = newObj;

  for (let i = 0; i < parts.length - 1; i++) {
    const part = parts[i];
    if (current[part] === undefined || current[part] === null || typeof current[part] !== "object") {
      current[part] = {};
    } else {
      current[part] = { ...current[part] };
    }
    current = current[part];
  }

  const lastPart = parts[parts.length - 1];
  current[lastPart] = value;
  return newObj;
}
