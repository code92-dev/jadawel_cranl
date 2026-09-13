import { readFile } from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const projectRoot = path.resolve(
  path.dirname(fileURLToPath(import.meta.url)),
  '..'
)

export const localeDirectories = [
  'locales',
  'modules/arabase/locales',
  'modules/automation/locales',
  'modules/builder/locales',
  'modules/core/locales',
  'modules/dashboard/locales',
  'modules/database/locales',
  'modules/integrations/locales',
]

export const allowedIdenticalValues = new Set([
  'AI',
  'API',
  'Airtable',
  'Anthropic',
  'CSV',
  'Excel',
  'HTTP',
  'HTTPS',
  'HTML',
  'JSON',
  'Jadawel',
  'Markdown',
  'Mistral',
  'Nafath',
  'Ollama',
  'OpenAI',
  'OpenRouter',
  'PostgreSQL',
  'SMTP',
  'SMTP - {host}:{port}',
  'Slack',
  'URL',
  'UUID',
  'Webhooks',
  'Webhooks {name}',
  'XML',
  '2FA',
  'smtp.gmail.com',
  "your-email{'@'}example.com",
  "sender{'@'}example.com",
  '587',
  '0-23',
  '0-59',
  '15',
  '1-31',
  '{prefixName}: {schemaProperty}',
  'yyyy-mm-dd',
])

// Keys whose value is a literal code sample — a query string, a config file
// name, a moment.js format token. Translating any of it produces something the
// user cannot paste and that silently does not work, so these are exempt from
// the "must differ from English" and "must contain Arabic" checks. Earlier
// passes had turned `?prefill_rating=3` into `?prefill_rated=3` and the date
// format tokens into 'يوم/شهر/سنة', both of which are broken input.
export const literalValueKeyPattern = /(^|\.)codeSnippet$/

export function parseLocaleJson(contents, filename = 'locale file') {
  try {
    return JSON.parse(contents)
  } catch (error) {
    throw new Error(`${filename} is not valid JSON: ${error.message}`, {
      cause: error,
    })
  }
}

export function flattenLocale(locale, prefix = '', flattened = new Map()) {
  for (const [key, value] of Object.entries(locale)) {
    const fullKey = prefix ? `${prefix}.${key}` : key

    if (value !== null && typeof value === 'object') {
      flattenLocale(value, fullKey, flattened)
    } else {
      flattened.set(fullKey, value)
    }
  }

  return flattened
}

function tokens(value) {
  const patterns = [
    /\{[^{}]+\}/g,
    /@(?:\.|:)[\w.-]+/g,
    /<\/?[A-Za-z][^>]*>/g,
    /\\[nrt"'\\]/g,
  ]

  return patterns
    .flatMap((pattern) =>
      Array.from(value.matchAll(pattern), ([token]) => token)
    )
    .sort()
}

function valuesAreEqual(left, right) {
  return (
    left.length === right.length &&
    left.every((value, index) => value === right[index])
  )
}

function issue(type, key, details = {}) {
  return { type, key, ...details }
}

/**
 * CLDR plural categories Arabic uses and English does not.
 *
 * Count messages are stored as one key per category (see `utils/plural`), and
 * Arabic has six where English has two. `dashboardApplication.rowCount.many` is
 * therefore expected to have no English twin — it is a category the language
 * needs, not a stray key. `zero`, `one` and `other` are deliberately absent from
 * this list: those exist in both files and must stay paired.
 */
const ARABIC_ONLY_PLURAL_CATEGORIES = new Set(['two', 'few', 'many'])

function isArabicOnlyPluralCategory(key) {
  const category = key.split('.').pop()
  return ARABIC_ONLY_PLURAL_CATEGORIES.has(category)
}

export function validateLocalePair(
  englishLocale,
  arabicLocale,
  { allowIdentical = allowedIdenticalValues } = {}
) {
  const english = flattenLocale(englishLocale)
  const arabic = flattenLocale(arabicLocale)
  const issues = []

  for (const [key, englishValue] of english) {
    if (!arabic.has(key)) {
      issues.push(issue('missing', key))
      continue
    }

    const arabicValue = arabic.get(key)
    if (typeof englishValue !== 'string' || typeof arabicValue !== 'string') {
      issues.push(
        issue('non-string', key, {
          englishType: typeof englishValue,
          arabicType: typeof arabicValue,
        })
      )
      continue
    }

    const isBlank = !arabicValue.trim()
    const hasTemporaryMarker =
      /\b(?:TODO|TBD|machine translation|translation pending|translate me)\b/i.test(
        arabicValue
      )

    if (isBlank) {
      issues.push(issue('blank', key))
    }

    if (hasTemporaryMarker) {
      issues.push(issue('marker', key))
    }

    const englishTokens = tokens(englishValue)
    const arabicTokens = tokens(arabicValue)
    if (!valuesAreEqual(englishTokens, arabicTokens)) {
      issues.push(issue('token-mismatch', key, { englishTokens, arabicTokens }))
    }

    const isLiteralValue = literalValueKeyPattern.test(key)

    if (
      englishValue === arabicValue &&
      !allowIdentical.has(arabicValue) &&
      !isLiteralValue
    ) {
      issues.push(issue('identical-to-english', key, { value: arabicValue }))
    }

    if (
      !isBlank &&
      !hasTemporaryMarker &&
      !/[\u0600-\u06ff]/.test(arabicValue) &&
      !allowIdentical.has(arabicValue) &&
      !isLiteralValue
    ) {
      issues.push(issue('missing-arabic-script', key, { value: arabicValue }))
    }
  }

  for (const key of arabic.keys()) {
    if (!english.has(key) && !isArabicOnlyPluralCategory(key)) {
      issues.push(issue('unexpected', key))
    }

    if (key === '_note' || key.startsWith('_note.')) {
      issues.push(issue('sentinel', key))
    }
  }

  return {
    englishKeyCount: english.size,
    translatedKeyCount:
      english.size - issues.filter(({ type }) => type === 'missing').length,
    issues,
  }
}

function parseArguments(arguments_) {
  return {
    baseline: arguments_.includes('--baseline'),
    strict: arguments_.includes('--strict'),
  }
}

function printIssues(issues) {
  for (const { type, key, ...details } of issues) {
    const suffix = Object.keys(details).length
      ? ` ${JSON.stringify(details)}`
      : ''
    console.error(`  ${type}: ${key}${suffix}`)
  }
}

async function loadJson(relativePath) {
  const filename = path.join(projectRoot, relativePath)
  return parseLocaleJson(await readFile(filename, 'utf8'), relativePath)
}

async function main() {
  const { baseline, strict } = parseArguments(process.argv.slice(2))
  const baselineLimits = baseline
    ? await loadJson('scripts/locale-parity-baseline.json')
    : null
  const totals = { english: 0, translated: 0, missing: 0 }
  let failed = false

  for (const directory of localeDirectories) {
    const [english, arabic] = await Promise.all([
      loadJson(path.join(directory, 'en.json')),
      loadJson(path.join(directory, 'ar.json')),
    ])
    const result = validateLocalePair(english, arabic)
    const missing = result.issues.filter(({ type }) => type === 'missing')
    const blockingIssues = result.issues.filter(
      ({ type }) => type !== 'missing'
    )
    const limit = baselineLimits?.maximumMissingKeys?.[directory]

    totals.english += result.englishKeyCount
    totals.translated += result.translatedKeyCount
    totals.missing += missing.length

    console.log(
      `${directory}: ${result.translatedKeyCount}/${result.englishKeyCount} translated; ${missing.length} missing`
    )

    if (blockingIssues.length) {
      printIssues(blockingIssues)
      failed = true
    }

    if (strict && missing.length) {
      printIssues(missing)
      failed = true
    }

    if (baseline && (limit === undefined || missing.length > limit)) {
      console.error(
        `  missing-key regression: ${missing.length} missing keys exceeds the approved baseline of ${limit ?? 0}`
      )
      failed = true
    }
  }

  const coverage = ((totals.translated / totals.english) * 100).toFixed(1)
  console.log(
    `Total: ${totals.translated}/${totals.english} translated (${coverage}%); ${totals.missing} missing`
  )

  if (failed) {
    process.exitCode = 1
  }
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  await main()
}
