import { DecoratorValueProviderType } from '@jadawel/modules/database/decoratorValueProviders'
import { SingleSelectFieldType } from '@jadawel/modules/database/fieldTypes'
import { BackgroundColorDecoratorType } from '@jadawel/modules/arabase/decorators/backgroundColor'
import { LeftBorderColorDecoratorType } from '@jadawel/modules/arabase/decorators/leftBorderColor'
import SingleSelectColorForm from '@jadawel/modules/arabase/components/SingleSelectColorForm'

const COLOR_PATTERN = /^[a-z-]+$/

/**
 * Resolves a row color from the color of its single select option.
 *
 * OSS counterpart of the backend `single_select_color` provider. Reads the
 * already-loaded row value (`field_<id>` → `{ color }`), so coloring costs
 * no extra query per row. Unknown fields and missing colors resolve to
 * `null`, which renders the row undecorated.
 */
export class SingleSelectColorValueProviderType extends DecoratorValueProviderType {
  static getType() {
    return 'single_select_color'
  }

  getName() {
    return this.$t('rowColoring.singleSelectName')
  }

  getDescription() {
    return this.$t('rowColoring.singleSelectDescription')
  }

  getIconClass() {
    return 'iconoir-palette'
  }

  getCompatibleDecoratorTypes() {
    return [BackgroundColorDecoratorType, LeftBorderColorDecoratorType]
  }

  getFormComponent() {
    return SingleSelectColorForm
  }

  getDefaultConfiguration({ fields }) {
    const first = (fields || []).find(
      (field) => field.type === SingleSelectFieldType.getType()
    )
    return { field_id: first ? first.id : null }
  }

  getValue({ options, fields, row }) {
    const field = (fields || []).find((field) => field.id === options?.field_id)
    if (!field) {
      return null
    }
    const color = row?.[`field_${field.id}`]?.color
    return typeof color === 'string' && COLOR_PATTERN.test(color) ? color : null
  }
}
