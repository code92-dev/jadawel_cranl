/**
 * Flatten a DRF error response into one readable line.
 *
 * The admin endpoints reject invalid input with field errors such as
 * `{"owner": "choose_id_or_email"}` or `{"responsible_email":
 * "user_not_found"}`. The codes are stable, machine-readable and not
 * translated, so they are shown verbatim next to the translated banner: an
 * untranslated code an admin can act on beats a 400 visible only in the
 * browser console.
 */
export function describeApiError(error) {
  const data = error?.response?.data;
  if (!data) return "";
  if (typeof data === "string") return data;
  const parts = [];
  const walk = (value, field) => {
    if (Array.isArray(value)) {
      value.forEach((item) => walk(item, field));
    } else if (value && typeof value === "object") {
      Object.entries(value).forEach(([key, item]) =>
        walk(item, field ? `${field}.${key}` : key),
      );
    } else if (value !== null && value !== undefined && value !== "") {
      parts.push(field ? `${field}: ${value}` : String(value));
    }
  };
  walk(data, "");
  return parts.join(" · ");
}
