<template>
  <div class="conditional-color-form">
    <p v-if="!readOnly" class="conditional-color-form__help">
      {{ $t('rowColoring.conditionsHelp') }}
    </p>
    <div
      v-for="(rule, index) in rules"
      :key="rule.id"
      class="conditional-color-form__rule"
    >
      <div class="conditional-color-form__header">
        <a
          :ref="'color-select-' + index"
          class="conditional-color-form__color"
          :class="'background-color--' + rule.color"
          :title="$t('rowColoring.chooseColor')"
          @click="openColor(index)"
        ></a>
        <Dropdown
          :value="rule.operator"
          :disabled="readOnly"
          :show-search="false"
          :fixed-items="true"
          class="conditional-color-form__operator"
          @input="updateRuleOperator(rule, $event)"
        >
          <DropdownItem
            :name="$t('viewFilterContext.and')"
            value="AND"
          ></DropdownItem>
          <DropdownItem
            :name="$t('viewFilterContext.or')"
            value="OR"
          ></DropdownItem>
        </Dropdown>
        <span
          v-if="isDefaultRule(rule)"
          class="conditional-color-form__default-badge"
        >
          {{ $t('rowColoring.defaultRuleLabel') }}
        </span>
        <ButtonIcon
          v-if="rules.length > 1"
          tag="a"
          icon="iconoir-cancel"
          :title="$t('rowColoring.removeRule')"
          @click.stop.prevent="removeRule(index)"
        ></ButtonIcon>
      </div>
      <ViewFieldConditionsForm
        :filters="rule.filters"
        :filter-groups="rule.filter_groups"
        :disable-filter="readOnly"
        :filter-type="rule.operator"
        :view="view"
        :fields="fields"
        :read-only="readOnly"
        :full-width="true"
        :variant="'dark'"
        :sorted="true"
        :can-add-filter-groups="true"
        @add-filter="addFilter(rule, $event)"
        @add-filter-group="addFilterGroup(rule, $event)"
        @update-filter="updateFilter(rule, $event)"
        @delete-filter="deleteFilter(rule, $event)"
        @update-filter-type="updateFilterType(rule, $event)"
        @delete-filter-group="deleteFilterGroup(rule, $event)"
      />
      <div
        v-if="rule.filters.length === 0 && rule.filter_groups.length === 0"
        class="conditional-color-form__actions"
      >
        <ButtonText icon="iconoir-plus" tag="a" @click="addFilter(rule)">
          {{ $t('viewFieldConditionsForm.addCondition') }}
        </ButtonText>
      </div>
    </div>
    <ButtonText icon="iconoir-plus" tag="a" @click="addRule()">
      {{ $t('rowColoring.addRule') }}
    </ButtonText>
    <ColorSelectContext
      ref="colorContext"
      @selected="updateColor"
    ></ColorSelectContext>
  </div>
</template>

<script>
import { ulid } from 'ulid'
import { clone } from '@jadawel/modules/core/utils/object'
import { randomColor } from '@jadawel/modules/core/utils/colors'
import ColorSelectContext from '@jadawel/modules/core/components/ColorSelectContext'
import ViewFieldConditionsForm from '@jadawel/modules/database/components/view/ViewFieldConditionsForm'

export default {
  name: 'ConditionalColorForm',
  components: { ColorSelectContext, ViewFieldConditionsForm },
  props: {
    view: { type: Object, required: true },
    table: { type: Object, required: true },
    database: { type: Object, required: true },
    fields: { type: Array, required: true },
    readOnly: { type: Boolean, required: true },
    options: { type: Object, required: true },
  },
  emits: ['update'],
  data() {
    return {
      // Which rule's swatch opened the color context.
      colorContextRuleId: null,
    }
  },
  computed: {
    rules() {
      return this.options.colors || []
    },
  },
  methods: {
    emitUpdate(colors) {
      this.$emit('update', { colors })
    },
    isDefaultRule(rule) {
      return rule.filters.length === 0 && rule.filter_groups.length === 0
    },
    openColor(index) {
      this.colorContextRuleId = this.rules[index].id
      this.$refs.colorContext.setActive(this.rules[index].color)
      this.$refs.colorContext.toggle(
        this.$refs['color-select-' + index][0],
        'bottom',
        'left',
        4
      )
    },
    updateColor(color) {
      const rule = this.rules.find(
        (rule) => rule.id === this.colorContextRuleId
      )
      if (rule) {
        rule.color = color
        this.emitUpdate(this.rules)
      }
    },
    generateCompatibleCondition(filterGroupId = null) {
      const filterTypes = this.$registry.getAll('viewFilter')
      const field = this.fields.find((field) =>
        Object.values(filterTypes).some((filterType) =>
          filterType.fieldIsCompatible(field)
        )
      )
      const compatibleType = Object.values(filterTypes).find((filterType) =>
        filterType.fieldIsCompatible(field)
      )
      const condition = {
        id: ulid(),
        field: field.id,
        type: compatibleType.type,
        value: '',
      }
      if (filterGroupId !== null) {
        condition.group = filterGroupId
      }
      return condition
    },
    addRule() {
      // The new rule starts as the default color rule: no conditions yet,
      // first-match-wins puts it last so existing rules keep precedence.
      this.emitUpdate([
        ...this.rules,
        {
          id: ulid(),
          filters: [],
          filter_groups: [],
          operator: 'AND',
          color: randomColor(),
        },
      ])
    },
    removeRule(index) {
      this.emitUpdate(this.rules.filter((_, i) => i !== index))
    },
    updateRuleOperator(rule, value) {
      rule.operator = value
      this.emitUpdate(this.rules)
    },
    addFilter(rule, { filterGroupId = null } = {}) {
      const condition = this.generateCompatibleCondition(filterGroupId)
      rule.filters.push(condition)
      this.emitUpdate(this.rules)
    },
    addFilterGroup(rule, { parentGroupId = null } = {}) {
      const group = {
        id: ulid(),
        filter_type: 'AND',
        parent_group: parentGroupId,
      }
      rule.filter_groups.push(group)
      rule.filters.push(this.generateCompatibleCondition(group.id))
      this.emitUpdate(this.rules)
    },
    updateFilterType(rule, { value, filterGroup }) {
      if (filterGroup === undefined) {
        rule.operator = value
      } else {
        rule.filter_groups = clone(rule.filter_groups.slice()).map((group) => {
          return group.id === filterGroup.id
            ? { ...group, filter_type: value }
            : group
        })
      }
      this.emitUpdate(this.rules)
    },
    updateFilter(rule, condition) {
      rule.filters = rule.filters.map((filter) => {
        return filter.id === condition.filter.id
          ? { ...filter, ...condition.values }
          : filter
      })
      this.emitUpdate(this.rules)
    },
    deleteFilter(rule, condition) {
      rule.filters = rule.filters.filter((filter) => filter.id !== condition.id)
      this.emitUpdate(this.rules)
    },
    deleteFilterGroup(rule, { group }) {
      const groupsToRemove = [group.id]
      const removeChildren = (parentId) => {
        for (const child of rule.filter_groups.filter(
          (candidate) => candidate.parent_group === parentId
        )) {
          groupsToRemove.push(child.id)
          removeChildren(child.id)
        }
      }
      removeChildren(group.id)
      rule.filters = rule.filters.filter(
        (filter) => !groupsToRemove.includes(filter.group)
      )
      rule.filter_groups = rule.filter_groups.filter(
        (candidate) => !groupsToRemove.includes(candidate.id)
      )
      this.emitUpdate(this.rules)
    },
  },
}
</script>
