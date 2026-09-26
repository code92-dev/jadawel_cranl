import { ViewDecoratorType } from '@jadawel/modules/database/viewDecorators'

/**
 * Shared base of the row coloring decorators (`background_color` and
 * `left_border_color`). Both decorate the same views and allow one decoration
 * of their type per view. A subclass supplies its type, texts, image,
 * component and place, plus the i18n key returned by `getAlreadyAddedKey`.
 */
export class ColorRowDecoratorType extends ViewDecoratorType {
  /**
   * The i18n key of the reason shown when the view already has a decoration
   * of this type.
   */
  getAlreadyAddedKey() {
    throw new Error(
      'Not implemented error. This decorator should return an i18n key.'
    )
  }

  isCompatible(view) {
    return ['grid', 'gallery', 'kanban'].includes(view?.type)
  }

  canAdd({ view }) {
    const exists = (view?.decorations || []).some(
      (decoration) => decoration.type === this.getType()
    )
    if (exists) {
      return [false, this.$t(this.getAlreadyAddedKey())]
    }
    return [true, '']
  }
}
