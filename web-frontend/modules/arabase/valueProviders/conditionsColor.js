import { DecoratorValueProviderType } from '@jadawel/modules/database/decoratorValueProviders'
import { createFiltersTree } from '@jadawel/modules/database/utils/view'
import { BackgroundColorDecoratorType } from '@jadawel/modules/arabase/decorators/backgroundColor'
import { LeftBorderColorDecoratorType } from '@jadawel/modules/arabase/decorators/leftBorderColor'
import ConditionalColorForm from '@jadawel/modules/arabase/components/ConditionalColorForm'

const COLOR_PATTERN = /^[a-z-]+$/

/**
 * Resolves a row color from the first matching list of conditions.
 *
 * OSS counterpart of the backend `conditional_color` provider. The
 * configuration is
 * `{ colors: [{ filters, filter_groups, operator, color }] }` — the same
 * shape the Airtable import mapping emits — and conditions reuse the view
 * filter operator set, so the same registry implementations evaluate them.
 *
 * Rules are evaluated in stored order and the first match wins. A rule
 * with no conditions matches every row, so a trailing empty rule acts as
 * the default color for unmatched rows. Rows never match rules whose
 * fields no longer exist, which renders them undecorated instead of
 * crashing the grid.
 */
export class ConditionalColorValueProviderType extends DecoratorValueProviderType {
  static getType() {
    return 'conditional_color'
  }

  getName() {
    return this.$t('rowColoring.conditionsName')
  }

  getDescription() {
    return this.$t('rowColoring.conditionsDescription')
  }

  getIconClass() {
    return 'iconoir-filter'
  }

  getCompatibleDecoratorTypes() {
    return [BackgroundColorDecoratorType, LeftBorderColorDecoratorType]
  }

  getFormComponent() {
    return ConditionalColorForm
  }

  getDefaultConfiguration() {
    return { colors: [] }
  }

  /**
   * Builds (and caches) the filter tree for every rule of a configuration.
   * The cache is keyed on the options object, so editing a rule invalidates
   * it and colors update as soon as the new configuration is in the store.
   */
  getRuleTrees(options) {
    if (!options) {
      return []
    }
    if (!this._treeCache) {
      this._treeCache = new WeakMap()
    }
    const cached = this._treeCache.get(options)
    if (cached) {
      return cached
    }
    const trees = (options.colors || [])
      .filter((rule) => rule && ['AND', 'OR'].includes(rule.operator))
      .map((rule) => ({
        rule,
        tree: createFiltersTree(
          rule.operator,
          rule.filters || [],
          rule.filter_groups || []
        ),
      }))
    this._treeCache.set(options, trees)
    return trees
  }

  getValue({ options, fields, row, $registry }) {
    const registry = $registry || this.app.$registry
    if (!registry) {
      return null
    }
    for (const { rule, tree } of this.getRuleTrees(options)) {
      try {
        if (tree.matches(registry, fields, row)) {
          return typeof rule.color === 'string' &&
            COLOR_PATTERN.test(rule.color)
            ? rule.color
            : null
        }
      } catch (error) {
        // A rule referencing a field or filter type that no longer exists
        // must never break row rendering; treat it as no-match.
        continue
      }
    }
    return null
  }
}
