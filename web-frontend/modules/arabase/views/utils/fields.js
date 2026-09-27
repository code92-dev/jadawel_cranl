/**
 * The fields a page receives, in its order. Shared by the view type (core's
 * share popup reads it) and the component that builds the page's payload.
 */
export function visibleFieldsInOrder(fields, fieldOptions) {
  return fields
    .filter((field) => !fieldOptions[field.id]?.hidden)
    .sort(
      (a, b) =>
        (fieldOptions[a.id]?.order ?? 0) - (fieldOptions[b.id]?.order ?? 0) ||
        a.id - b.id
    )
}
