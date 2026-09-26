/**
 * The database applications that belong to a workspace. An application may
 * carry its workspace as a nested object or as a flat `workspace_id`.
 */
export function databasesInWorkspace(applications, workspaceId) {
  return applications.filter(
    (application) =>
      application.type === 'database' &&
      (application.workspace?.id || application.workspace_id) === workspaceId
  )
}

/**
 * A protected-field selection entry. The `database` key is added only when a
 * database is given; without one the key is absent rather than undefined.
 */
export function selectionEntry(field, table, database) {
  const entry = {
    id: field.id,
    name: field.name,
    type: field.type,
    table: { id: table.id, name: table.name },
  }
  if (database) {
    entry.database = { id: database.id, name: database.name }
  }
  return entry
}
