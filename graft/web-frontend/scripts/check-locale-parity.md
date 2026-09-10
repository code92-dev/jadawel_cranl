# web-frontend/scripts/check-locale-parity.mjs

- parseLocaleJson · function · L68-L74 — function parseLocaleJson(contents, filename = 'locale file')
- flattenLocale · function · L76-L88 — function flattenLocale(locale, prefix = '', flattened = new Map())
- tokens · function · L90-L103 — function tokens(value)
- valuesAreEqual · function · L105-L110 — function valuesAreEqual(left, right)
- issue · function · L112-L114 — function issue(type, key, details = {})
- isArabicOnlyPluralCategory · function · L127-L130 — function isArabicOnlyPluralCategory(key)
- validateLocalePair · function · L132-L215 — function validateLocalePair( englishLocale, arabicLocale, { allowIdentical = allowedIdenticalValues } = {} )
- parseArguments · function · L217-L222 — function parseArguments(arguments_)
- printIssues · function · L224-L231 — function printIssues(issues)
- loadJson · function · L233-L236 — async function loadJson(relativePath)
- main · function · L238-L292 — async function main()
