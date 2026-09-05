import { ViewDecoratorType } from '@jadawel/modules/database/viewDecorators'
import LeftBorderColorDecorator from '@jadawel/modules/arabase/components/LeftBorderColorDecorator'

const IMAGE =
  'data:image/svg+xml;utf8,' +
  encodeURIComponent(
    "<svg xmlns='http://www.w3.org/2000/svg' width='72' height='48'>" +
      "<rect x='4' y='4' width='8' height='40' fill='#90caf9'/></svg>"
  )

/**
 * Paints a subtle color bar on the record's inline-start edge.
 *
 * OSS counterpart of the backend `left_border_color` decorator type
 * registered in `arabase.row_coloring`. "Left" is the logical inline-start
 * edge, so the bar renders on the right in Arabic (RTL) views. It shares
 * the `first_cell` place with core's decoration renderer: the grid draws it
 * inside the row details cell, cards pin it to their start edge.
 */
export class LeftBorderColorDecoratorType extends ViewDecoratorType {
  static getType() {
    return 'left_border_color'
  }

  getName() {
    return this.$t('rowColoring.leftBorderColorName')
  }

  getDescription() {
    return this.$t('rowColoring.leftBorderColorDescription')
  }

  getImage() {
    return IMAGE
  }

  isCompatible(view) {
    return ['grid', 'gallery'].includes(view?.type)
  }

  canAdd({ view }) {
    const exists = (view?.decorations || []).some(
      (decoration) => decoration.type === this.getType()
    )
    if (exists) {
      return [false, this.$t('rowColoring.leftBorderAlreadyAdded')]
    }
    return [true, '']
  }

  getComponent() {
    return LeftBorderColorDecorator
  }

  getPlace() {
    return 'first_cell'
  }
}
