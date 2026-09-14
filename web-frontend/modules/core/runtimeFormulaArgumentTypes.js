import {
  ensureString,
  ensureNumeric,
  ensureDateTime,
  ensureObject,
  ensureBoolean,
  ensureArray,
  ensureDuration,
} from '@jadawel/modules/core/utils/validator'
import moment from '@jadawel/modules/core/moment'
import {
  Timedelta,
  isValidDatetimeFormat,
  parseDurationString,
} from '@jadawel/modules/core/utils/date'
import { isValidDurationFormat } from '@jadawel/modules/core/utils/duration'
export { Timedelta, parseDurationString }

const VALID_THOUSAND_SEPARATORS = new Set([',', '.', ' ', ''])
const VALID_DECIMAL_SEPARATORS = new Set([',', '.'])

export class JadawelRuntimeFormulaArgumentType {
  constructor({ optional = false } = {}) {
    this.optional = optional
  }

  /**
   * This function tests if a given value is compatible with its type
   * @param value -  The value being tests
   * @returns {boolean} - If the value is of a valid type
   */
  test(value) {
    return true
  }

  /**
   * This function allows you to parse any given value to its type. This can be useful
   * if the argument is of the wrong type but can be parsed to the correct type.
   *
   * This can also be used to transform the data before it gets to the function call.
   *
   * @param value - The value that is being parsed
   * @returns {*} - The parsed value
   */
  parse(value) {
    return value
  }

  /**
   * This function returns a specific human-friendly error message if the
   * value for the type is invalid. Defaults to returning null.
   * @param value - The value that is incorrect.
   * @param i18n - The i18n instance.
   * @returns {string|null} - The human-friendly error message.
   */
  getErrorMessage(value, i18n) {
    return null
  }
}

export class NumberJadawelRuntimeFormulaArgumentType extends JadawelRuntimeFormulaArgumentType {
  constructor(options = {}) {
    super(options)
    this.castToInt = options.castToInt ?? false
    this.castToFloat = options.castToFloat ?? false
  }

  test(value) {
    if (value === undefined) {
      return false
    }

    try {
      ensureNumeric(value)
      return true
    } catch (e) {
      return false
    }
  }

  parse(value) {
    const val = ensureNumeric(value)
    if (this.castToInt) {
      return Math.trunc(val)
    } else if (this.castToFloat) {
      return parseFloat(val)
    }
    return val
  }

  getErrorMessage(value, i18n) {
    return i18n.t('runtimeFormulaTypeErrors.invalidNumber', { value })
  }
}

export class TextJadawelRuntimeFormulaArgumentType extends JadawelRuntimeFormulaArgumentType {
  test(value) {
    return typeof value.toString === 'function'
  }

  parse(value) {
    return ensureString(value)
  }
}

export class DateTimeJadawelRuntimeFormulaArgumentType extends JadawelRuntimeFormulaArgumentType {
  test(value) {
    if (value instanceof Date) {
      return true
    }
    try {
      ensureDateTime(value, { useStrict: false })
      return true
    } catch (e) {
      return false
    }
  }

  parse(value) {
    return ensureDateTime(value, { useStrict: false })
  }
}

export class ObjectJadawelRuntimeFormulaArgumentType extends JadawelRuntimeFormulaArgumentType {
  test(value) {
    if (value instanceof Object) {
      return true
    }

    try {
      ensureObject(value)
      return true
    } catch (e) {
      return false
    }
  }

  parse(value) {
    return ensureObject(value)
  }
}

export class ArrayJadawelRuntimeFormulaArgumentType extends JadawelRuntimeFormulaArgumentType {
  test(value) {
    try {
      ensureArray(value)
      return true
    } catch (e) {
      return false
    }
  }

  parse(value) {
    return ensureArray(value)
  }
}

export class ArrayOfNumbersJadawelRuntimeFormulaArgumentType extends JadawelRuntimeFormulaArgumentType {
  test(value) {
    try {
      value = ensureArray(value)
    } catch (e) {
      return false
    }
    try {
      value.forEach((item) => ensureNumeric(item))
      return true
    } catch (e) {
      return false
    }
  }

  parse(value) {
    value = ensureArray(value)
    return value.map((item) => ensureNumeric(item))
  }
}

export class BooleanJadawelRuntimeFormulaArgumentType extends JadawelRuntimeFormulaArgumentType {
  test(value) {
    try {
      ensureBoolean(value, { useStrict: false })
      return true
    } catch (e) {
      return false
    }
  }

  parse(value) {
    return ensureBoolean(value, { useStrict: false })
  }
}

export class TimezoneJadawelRuntimeFormulaArgumentType extends JadawelRuntimeFormulaArgumentType {
  test(value) {
    if (value == null || typeof value.toString !== 'function') {
      return false
    }

    return moment.tz.names().includes(value)
  }

  parse(value) {
    return ensureString(value)
  }

  getErrorMessage(value, i18n) {
    return i18n.t('runtimeFormulaTypeErrors.invalidTimezone', { value })
  }
}

export class AnyJadawelRuntimeFormulaArgumentType extends JadawelRuntimeFormulaArgumentType {
  test(value) {
    return true
  }

  parse(value) {
    return value
  }
}

export class ThousandSeparatorJadawelRuntimeFormulaArgumentType extends JadawelRuntimeFormulaArgumentType {
  test(value) {
    if (typeof value !== 'string') return false
    return VALID_THOUSAND_SEPARATORS.has(value)
  }

  parse(value) {
    return ensureString(value)
  }

  getErrorMessage(value, i18n) {
    return i18n.t('runtimeFormulaTypeErrors.invalidThousandSeparator', {
      value,
    })
  }
}

export class DecimalSeparatorJadawelRuntimeFormulaArgumentType extends JadawelRuntimeFormulaArgumentType {
  test(value) {
    if (typeof value !== 'string') return false
    return VALID_DECIMAL_SEPARATORS.has(value)
  }

  parse(value) {
    return ensureString(value)
  }

  getErrorMessage(value, i18n) {
    return i18n.t('runtimeFormulaTypeErrors.invalidDecimalSeparator', { value })
  }
}

export class TimedeltaJadawelRuntimeFormulaArgumentType extends JadawelRuntimeFormulaArgumentType {
  test(value) {
    return value instanceof Timedelta
  }

  parse(value) {
    return value
  }
}

export class DurationJadawelRuntimeFormulaArgumentType extends JadawelRuntimeFormulaArgumentType {
  test(value) {
    try {
      ensureDuration(value)
      return true
    } catch (e) {
      return false
    }
  }

  parse(value) {
    return ensureDuration(value)
  }

  getErrorMessage(value, i18n) {
    return i18n.t('runtimeFormulaTypeErrors.invalidDuration', { value })
  }
}

export class NullableDurationJadawelRuntimeFormulaArgumentType extends DurationJadawelRuntimeFormulaArgumentType {
  // A duration argument that also accepts null, for functions whose null
  // contract is "null in, null out" (e.g. `duration_format(null(), 'h:mm')`
  // must return null). Duration validation itself is not weakened: any
  // non-null value still has to parse as a duration. Mirrors the backend's
  // NullableDurationJadawelRuntimeFormulaArgumentType.
  test(value) {
    if (value === null) {
      return true
    }
    return super.test(value)
  }

  parse(value) {
    if (value === null) {
      return null
    }
    return super.parse(value)
  }
}

export class DatetimeFormatJadawelRuntimeFormulaArgumentType extends JadawelRuntimeFormulaArgumentType {
  test(value) {
    return isValidDatetimeFormat(value)
  }

  parse(value) {
    return ensureString(value)
  }

  getErrorMessage(value, i18n) {
    return i18n.t('runtimeFormulaTypeErrors.invalidDatetimeFormat', { value })
  }
}

export class DurationFormatJadawelRuntimeFormulaArgumentType extends JadawelRuntimeFormulaArgumentType {
  test(value) {
    return isValidDurationFormat(value)
  }

  parse(value) {
    return ensureString(value)
  }

  getErrorMessage(value, i18n) {
    return i18n.t('runtimeFormulaTypeErrors.invalidDurationFormat', { value })
  }
}
