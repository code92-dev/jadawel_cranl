import {
  SAUDI_RIYAL,
  formatAggregate,
  formatNumber,
  intlLocale,
  isPlainNumber,
  isRiyal,
  riyalFormatted,
  riyalText,
  toNumber,
  withAffixes,
  withRiyal,
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
    expect(withAffixes('10', { suffix: 'USD' })).toBe('10 USD')
    expect(withAffixes('10', { suffix: '%' })).toBe('10%')
    expect(withAffixes('10', { prefix: '$' })).toBe('$10')
    expect(withAffixes('10', { prefix: 'EGP' })).toBe('EGP 10')
  })

  test('only a plain number is re-formatted; decorated values are kept', () => {
    expect(isPlainNumber('1610000')).toBe(true)
    expect(isPlainNumber('1,610,000.50')).toBe(true)
    expect(isPlainNumber('45%')).toBe(false)
    expect(isPlainNumber('2:30')).toBe(false)

    const options = { locale: 'en', compact: true, suffix: 'USD' }
    expect(formatAggregate('1610000.00', '1610000.00', options)).toBe(
      '1.6M USD'
    )
    expect(formatAggregate('0.45', '45%', options)).toBe('45% USD')
    expect(formatAggregate(null, null, options)).toBeNull()
  })

  describe('the Saudi riyal', () => {
    const sign = SAUDI_RIYAL
    const setDir = (dir) => {
      document.documentElement.dir = dir
    }
    afterEach(() => setDir(''))

    test('is U+20C1, however the unit is written', () => {
      expect(sign).toBe('⃁')
      for (const unit of [
        'ر.س',
        'ر.س.',
        'ر. س',
        'رس',
        'ريال',
        'ريال سعودي',
        'SAR',
        'sar',
        'SR',
        '﷼',
        sign,
      ]) {
        expect(isRiyal(unit)).toBe(true)
      }
      for (const unit of ['USD', '%', 'ريالات', 'SARAH', '']) {
        expect(isRiyal(unit)).toBe(false)
      }
    })

    test('the sign sits to the left of the amount in both directions', () => {
      // Before an English amount, after an Arabic one: right to left, the end
      // of the text is its left side.
      expect(withRiyal('1,000', false)).toBe(`${sign}\u00A01,000`)
      expect(withRiyal('1,000', true)).toBe(`1,000\u00A0${sign}`)

      setDir('rtl')
      expect(withAffixes('1.6 مليون', { suffix: 'ر.س' })).toBe(
        `1.6 مليون\u00A0${sign}`
      )
      setDir('ltr')
      expect(withAffixes('1.6M', { suffix: 'ر.س' })).toBe(`${sign}\u00A01.6M`)
      expect(withAffixes('1.6M', { prefix: 'SAR' })).toBe(`${sign}\u00A01.6M`)
    })

    test('a value its field already marked keeps a single sign', () => {
      setDir('ltr')
      expect(
        formatAggregate('1000', '1,000 SAR', { locale: 'en', suffix: 'ر.س' })
      ).toBe(`${sign}\u00A01,000`)
      expect(riyalFormatted('ر.س 50')).toBe(`${sign}\u00A050`)
    })

    test('titles and sentences swap only the abbreviations', () => {
      expect(riyalText('Total budget (SAR)')).toBe(
        `\u2068Total budget (${sign})\u2069`
      )
      expect(riyalText('الميزانية (ر.س)')).toBe(
        `\u2068الميزانية (${sign})\u2069`
      )
      expect(riyalText('المبلغ بالريال')).toBe('المبلغ بالريال')
      expect(riyalText('Riyadh, SARAH')).toBe('Riyadh, SARAH')
      expect(riyalText('')).toBe('')
    })
  })
})
