import { ViewDecoratorType } from '@jadawel/modules/database/viewDecorators'
import BackgroundColorDecorator from '@jadawel/modules/arabase/components/BackgroundColorDecorator'

const IMAGE =
  'data:image/svg+xml;utf8,' +
  encodeURIComponent(
    "<svg xmlns='http://www.w3.org/2000/svg' width='72' height='48'>" +
      "<rect x='4' y='4' width='64' height='40' rx='6' fill='#e3f2fd' " +
      "stroke='#90caf9'/></svg>"
  )

/**
 * Paints the whole record with the color resolved by the value provider.
 *
 * OSS counterpart of the backend `background_color` decorator type
 * registered in `arabase.row_coloring`. Works on every decorating view:
 * the grid paints the whole row, gallery cards paint the whole card.
 */
export class BackgroundColorDecoratorType extends ViewDecoratorType {
  static getType() {
    return 'background_color'
  }

  getName() {
    return this.$t('rowColoring.backgroundColorName')
  }

  getDescription() {
    return this.$t('rowColoring.backgroundColorDescription')
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
      return [false, this.$t('rowColoring.backgroundAlreadyAdded')]
    }
    return [true, '']
  }

  getComponent() {
    return BackgroundColorDecorator
  }

  getPlace() {
    return 'wrapper'
  }
}
