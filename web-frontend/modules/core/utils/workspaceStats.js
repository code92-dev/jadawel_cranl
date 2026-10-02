/**
 * Row totals are only shown when every database reported an exact count. One
 * database that gave up on counting would make the workspace total an
 * undercount presented as fact, which is worse than showing a dash.
 *
 * @param {Object} stats `{ [databaseId]: { rows_exact, ... } }`.
 * @returns {boolean} Whether the row counts of all databases can be added up.
 */
export function rowCountsAreExact(stats) {
  return Object.values(stats).every((stat) => stat.rows_exact)
}
