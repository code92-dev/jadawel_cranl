import { ColorRowDecoratorType } from '@jadawel/modules/arabase/decorators/colorRowDecorator'
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
export class BackgroundColorDecoratorType extends ColorRowDecoratorType {
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

  getAlreadyAddedKey() {
    return 'rowColoring.backgroundAlreadyAdded'
  }

  getComponent() {
    return BackgroundColorDecorator
  }

  getPlace() {
    return 'wrapper'
  }
}
