/**
 * The "add an element" gallery of the application builder: every element
 * grouped by what it is for, with a preview and one line on when to use it —
 * the same gallery the dashboards use for widgets. Replaces core's grid of
 * icons grouped as "base", "layout" and "form" elements.
 */
import button from '@jadawel/modules/arabase/assets/images/elements/button.svg?url'
import checkbox from '@jadawel/modules/arabase/assets/images/elements/checkbox.svg?url'
import choice from '@jadawel/modules/arabase/assets/images/elements/choice.svg?url'
import column from '@jadawel/modules/arabase/assets/images/elements/column.svg?url'
import datetimePicker from '@jadawel/modules/arabase/assets/images/elements/datetime_picker.svg?url'
import footer from '@jadawel/modules/arabase/assets/images/elements/footer.svg?url'
import formContainer from '@jadawel/modules/arabase/assets/images/elements/form_container.svg?url'
import header from '@jadawel/modules/arabase/assets/images/elements/header.svg?url'
import heading from '@jadawel/modules/arabase/assets/images/elements/heading.svg?url'
import iframe from '@jadawel/modules/arabase/assets/images/elements/iframe.svg?url'
import image from '@jadawel/modules/arabase/assets/images/elements/image.svg?url'
import inputText from '@jadawel/modules/arabase/assets/images/elements/input_text.svg?url'
import link from '@jadawel/modules/arabase/assets/images/elements/link.svg?url'
import menu from '@jadawel/modules/arabase/assets/images/elements/menu.svg?url'
import rating from '@jadawel/modules/arabase/assets/images/elements/rating.svg?url'
import ratingInput from '@jadawel/modules/arabase/assets/images/elements/rating_input.svg?url'
import recordSelector from '@jadawel/modules/arabase/assets/images/elements/record_selector.svg?url'
import repeat from '@jadawel/modules/arabase/assets/images/elements/repeat.svg?url'
import simpleContainer from '@jadawel/modules/arabase/assets/images/elements/simple_container.svg?url'
import table from '@jadawel/modules/arabase/assets/images/elements/table.svg?url'
import text from '@jadawel/modules/arabase/assets/images/elements/text.svg?url'
import { isSubstringOfStrings } from '@jadawel/modules/core/utils/string'

/** The sections, in the order the gallery shows them. */
export const ELEMENT_CATEGORIES = [
  'content',
  'data',
  'layout',
  'navigation',
  'forms',
]

/** Each element's section and preview. Order within a section follows this. */
export const ELEMENT_GALLERY = {
  heading: { category: 'content', tile: heading },
  text: { category: 'content', tile: text },
  image: { category: 'content', tile: image },
  rating: { category: 'content', tile: rating },
  iframe: { category: 'content', tile: iframe },
  table: { category: 'data', tile: table },
  repeat: { category: 'data', tile: repeat },
  column: { category: 'layout', tile: column },
  simple_container: { category: 'layout', tile: simpleContainer },
  header: { category: 'layout', tile: header },
  footer: { category: 'layout', tile: footer },
  menu: { category: 'navigation', tile: menu },
  link: { category: 'navigation', tile: link },
  button: { category: 'navigation', tile: button },
  form_container: { category: 'forms', tile: formContainer },
  input_text: { category: 'forms', tile: inputText },
  choice: { category: 'forms', tile: choice },
  checkbox: { category: 'forms', tile: checkbox },
  datetime_picker: { category: 'forms', tile: datetimePicker },
  record_selector: { category: 'forms', tile: recordSelector },
  rating_input: { category: 'forms', tile: ratingInput },
}

// Elements the fork has no entry for (a type added upstream later) still get
// a section from core's own category.
const CORE_CATEGORIES = {
  baseElement: 'content',
  layoutElement: 'layout',
  formElement: 'forms',
}

export function galleryEntry(elementType) {
  const type = elementType.getType()
  const known = ELEMENT_GALLERY[type]
  if (known) {
    return known
  }
  const category = CORE_CATEGORIES[elementType.category?.()] || 'content'
  return { category, tile: elementType.image }
}

/**
 * The gallery's sections: every element type matching `search` (by name,
 * core description or the gallery's own line), grouped and ordered. Sections
 * without a match are left out.
 */
export function gallerySections(elementTypes, { search = '', describe } = {}) {
  const order = Object.keys(ELEMENT_GALLERY)
  const position = (type) => {
    const index = order.indexOf(type.getType())
    return index === -1 ? order.length : index
  }
  const matching = elementTypes
    .filter((type) =>
      isSubstringOfStrings(
        [type.name, type.description, describe ? describe(type) : ''],
        search
      )
    )
    .sort((a, b) => position(a) - position(b))

  return ELEMENT_CATEGORIES.map((category) => ({
    category,
    elementTypes: matching.filter(
      (type) => galleryEntry(type).category === category
    ),
  })).filter((section) => section.elementTypes.length > 0)
}
