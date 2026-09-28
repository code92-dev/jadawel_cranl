import { Registerable } from '@jadawel/modules/core/registry'

const GENERIC_FAMILIES = ['serif', 'sans-serif', 'monospace', 'cursive']

/**
 * Jadawel fork: the CSS `font-family` value of a font family type.
 *
 * Upstream wrote `"Inter","sans-serif"`: a quoted generic name is a font
 * family called "sans-serif", which does not exist, and Inter has no Arabic
 * letters, so Arabic text in an app fell back to whatever the system had. The
 * app already ships IBM Plex Sans Arabic for its own interface; sans-serif
 * families now fall back to it, then to the real generic family.
 */
export function fontFamilyStack(fontFamilyType) {
  const generic = fontFamilyType.safeFont
  const stack = [`"${fontFamilyType.name}"`]
  if (generic === 'sans-serif') {
    stack.push('"IBM Plex Sans Arabic"')
  }
  stack.push(GENERIC_FAMILIES.includes(generic) ? generic : `"${generic}"`)
  return stack.join(',')
}

export class FontFamilyType extends Registerable {
  get name() {
    return ''
  }

  get safeFont() {
    return 'sans-serif'
  }

  get weights() {
    return ['regular', 'bold']
  }

  get defaultWeight() {
    return 'regular'
  }
}

export class InterFontFamilyType extends FontFamilyType {
  static getType() {
    return 'inter'
  }

  get name() {
    return 'Inter'
  }

  get weights() {
    return ['regular', 'medium', 'semi-bold', 'bold']
  }
}

export class ArialFontFamilyType extends FontFamilyType {
  static getType() {
    return 'arial'
  }

  get name() {
    return 'Arial'
  }
}

export class VerdanaFontFamilyType extends FontFamilyType {
  static getType() {
    return 'verdana'
  }

  get name() {
    return 'Verdana'
  }
}

export class TahomaFontFamilyType extends FontFamilyType {
  static getType() {
    return 'tahoma'
  }

  get name() {
    return 'Tahoma'
  }
}

export class TrebuchetMSFontFamilyType extends FontFamilyType {
  static getType() {
    return 'trebuchet_ms'
  }

  get name() {
    return 'Trebuchet MS'
  }
}

export class TimesNewRomanFontFamilyType extends FontFamilyType {
  static getType() {
    return 'times_new_roman'
  }

  get name() {
    return 'Times new roman'
  }

  get safeFont() {
    return 'serif'
  }
}

export class GeorgiaFontFamilyType extends FontFamilyType {
  static getType() {
    return 'georgia'
  }

  get name() {
    return 'Georgia'
  }

  get safeFont() {
    return 'serif'
  }
}

export class GaramondFontFamilyType extends FontFamilyType {
  static getType() {
    return 'garamond'
  }

  get name() {
    return 'Garamond'
  }

  get safeFont() {
    return 'serif'
  }
}

export class CourierNewFontFamilyType extends FontFamilyType {
  static getType() {
    return 'courier_new'
  }

  get name() {
    return 'Courier new'
  }

  get safeFont() {
    return 'monospace'
  }
}

export class BrushScriptMTFontFamilyType extends FontFamilyType {
  static getType() {
    return 'brush_script_mt'
  }

  get name() {
    return 'Brush Script MT'
  }

  get safeFont() {
    return 'cursive'
  }

  get weights() {
    return ['regular', 'bold']
  }
}
