import {
  formatAggregate,
  formatNumber,
  intlLocale,
  isPlainNumber,
  toNumber,
  withAffixes,
} from '@jadawel/modules/arabase/dashboard/format'

describe('dashboard number formatting', () => {
  test('numbers arrive as field-serialized strings', () => {
    expect(toNumber('1610000.00')).toBe(1610000)
    expect(toNumber(12)).toBe(12)
    for (const value of [null, '', 'abc', undefined, NaN, {}]) {
      expect(toNumber(value)).toBeNull()
    }
  })

  test('thousands are grouped; whole numbers stay whole', () => {
    expect(formatNumber('1610000', { locale: 'en' })).toBe('1,610,000')
    expect(formatNumber('12.3456', { locale: 'en' })).toBe('12.35')
    expect(formatNumber('12', { locale: 'en', decimals: 2 })).toBe('12.00')
    expect(formatNumber('abc', { locale: 'en' })).toBeNull()
  })

  test('compact notation shortens large numbers', () => {
    expect(formatNumber(1610000, { locale: 'en', compact: true })).toBe('1.6M')
    expect(formatNumber(950, { locale: 'en', compact: true })).toBe('950')
  })

  test('Arabic is formatted with Western digits', () => {
    expect(intlLocale('ar')).toBe('ar-u-nu-latn')
    expect(formatNumber(1610000, { locale: 'ar' })).toMatch(/^1.610.000$/)
    expect(formatNumber(1610000, { locale: 'ar', compact: true })).toMatch(
      /1.6/
    )
  })

  test('a unit sits beside the number, symbols tight against it', () => {
    expect(withAffixes('10', { suffix: 'SAR' })).toBe('10 SAR')
    expect(withAffixes('10', { suffix: '%' })).toBe('10%')
    expect(withAffixes('10', { prefix: '$' })).toBe('$10')
    expect(withAffixes('10', { prefix: 'ر.س' })).toBe('ر.س 10')
  })

  test('only a plain number is re-formatted; decorated values are kept', () => {
    expect(isPlainNumber('1610000')).toBe(true)
    expect(isPlainNumber('1,610,000.50')).toBe(true)
    expect(isPlainNumber('45%')).toBe(false)
    expect(isPlainNumber('2:30')).toBe(false)

    const options = { locale: 'en', compact: true, suffix: 'SAR' }
    expect(formatAggregate('1610000.00', '1610000.00', options)).toBe(
      '1.6M SAR'
    )
    expect(formatAggregate('0.45', '45%', options)).toBe('45% SAR')
    expect(formatAggregate(null, null, options)).toBeNull()
  })
})
