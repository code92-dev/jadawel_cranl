/**
 * Shared import file-size limit helpers.
 *
 * Every importer that reads a user-provided file (CSV, XML, JSON, Excel/ODS)
 * must enforce the same configured upload limit through this helper, so the
 * importer names cannot drift apart again.
 */

/**
 * The documented default when the runtime configuration is missing or not a
 * usable number. Mirrors the default in `modules/core/module.js`.
 */
export const DEFAULT_MAX_IMPORT_FILE_SIZE_MB = 512

/**
 * Resolves the configured import file size limit in megabytes.
 *
 * A missing, non-numeric, zero or negative runtime value falls back to the
 * documented default instead of silently disabling validation (a `NaN`
 * comparison is always false, which used to let oversized files through).
 *
 * @param {object} publicConfig The `config.public` runtime configuration.
 * @returns {number} The limit in megabytes, guaranteed to be a positive finite
 *   number.
 */
export function getMaxImportFileSizeMb(publicConfig) {
  // Number(), not parseInt(): parseInt prefix-parses, so a malformed value
  // like "999999abc" would silently become a 999999 MB limit. Anything that
  // is not exactly a positive finite number falls back to the default.
  const parsed = Number(publicConfig?.jadawelMaxImportFileSizeMb)
  if (!Number.isInteger(parsed) || parsed <= 0) {
    return DEFAULT_MAX_IMPORT_FILE_SIZE_MB
  }
  return parsed
}

/**
 * Returns whether a file exceeds the configured import size limit.
 *
 * @param {File} file The chosen file.
 * @param {object} publicConfig The `config.public` runtime configuration.
 * @returns {boolean} `true` when the file is larger than the limit.
 */
export function fileExceedsImportSizeLimit(file, publicConfig) {
  const maxSizeMb = getMaxImportFileSizeMb(publicConfig)
  return file.size > maxSizeMb * 1024 * 1024
}
