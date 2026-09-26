<template>
  <div class="kanban-view">
    <div v-if="!groupingField" class="kanban-view__empty">
      <p class="kanban-view__empty-title">
        {{ $t('kanbanView.chooseGroupingField') }}
      </p>
      <Dropdown ref="groupingDropdown" :value="null">
        <DropdownItem
          v-for="singleSelectField in singleSelectFields"
          :key="singleSelectField.id"
          :name="singleSelectField.name"
          :value="singleSelectField.id"
          @click="selectGroupingField(singleSelectField)"
        ></DropdownItem>
      </Dropdown>
      <p v-if="singleSelectFields.length === 0" class="kanban-view__empty-hint">
        {{ $t('kanbanView.noSingleSelectField') }}
      </p>
    </div>

    <div v-else ref="board" class="kanban-view__board">
      <div
        v-for="stack in stacks"
        :key="`stack-${stack.id}`"
        :ref="`stack-${stack.id}`"
        class="kanban-view__stack"
        :class="{
          'kanban-view__stack--drop-target':
            dragState && dragState.overStackId === stack.id,
        }"
      >
        <header class="kanban-view__stack-header">
          <span
            v-if="stack.color"
            class="kanban-view__stack-badge"
            :class="'background-color--' + stack.color"
          ></span>
          <span class="kanban-view__stack-title">{{
            stack.title || $t('kanbanView.emptyStack')
          }}</span>
          <span class="kanban-view__stack-count">{{
            getStackData(stack.id).count
          }}</span>
        </header>

        <div class="kanban-view__cards">
          <RowCard
            v-for="row in getStackData(stack.id).rows"
            :key="'card-' + row.id"
            :fields="cardFields"
            :row="row"
            :workspace-id="database.workspace.id"
            :decorations-by-place="decorationsByPlace"
            class="kanban-view__card"
            :class="{
              'kanban-view__card--dragging':
                dragState && dragState.rowId === row.id,
            }"
            @mousedown="cardDown($event, row, stack)"
          ></RowCard>

          <a
            v-if="getStackData(stack.id).hasNextPage"
            class="kanban-view__more"
            @click="loadMore(stack)"
          >
            <i class="iconoir-plus"></i>
            {{ $t('kanbanView.loadMore') }}
          </a>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { mapGetters } from 'vuex'
import { notifyIf } from '@jadawel/modules/core/utils/error'
import {
  sortFieldsByOrderAndIdFunction,
  filterVisibleFieldsFunction,
} from '@jadawel/modules/database/utils/view'
import RowCard from '@jadawel/modules/database/components/card/RowCard'
import Dropdown from '@jadawel/modules/core/components/Dropdown'
import DropdownItem from '@jadawel/modules/core/components/DropdownItem'
import viewHelpers from '@jadawel/modules/database/mixins/viewHelpers'
import viewDecoration from '@jadawel/modules/database/mixins/viewDecoration'

/**
 * The kanban board: one column per option of the view's single select field,
 * plus a column for rows without a value. Cards are rendered by the shared
 * `RowCard` (so decorations — row colors — apply), and dragging a card onto
 * another column updates the grouping field's value through the standard row
 * update API.
 *
 * Drag and drop is implemented with pointer events rather than the HTML5
 * drag API, so it works the same in every direction and keeps working under
 * `dir="rtl"`: the drop column is found with `document.elementFromPoint`,
 * which is direction-agnostic by construction.
 */
export default {
  name: 'KanbanView',
  components: { RowCard, Dropdown, DropdownItem },
  mixins: [viewHelpers, viewDecoration],
  props: {
    database: {
      type: Object,
      required: true,
    },
    table: {
      type: Object,
      required: true,
    },
    view: {
      type: Object,
      required: true,
    },
    fields: {
      type: Array,
      required: true,
    },
    readOnly: {
      type: Boolean,
      required: true,
    },
    storePrefix: {
      type: String,
      required: true,
    },
  },
  emits: ['refresh', 'selected-row'],
  data() {
    return {
      dragState: null,
    }
  },
  computed: {
    ...mapGetters({
      row: 'rowModalNavigation/getRow',
    }),
    stacks() {
      return this.$store.getters[this.storePrefix + 'view/kanban/getStacks']
    },
    groupingField() {
      const fieldId = this.view.single_select_field
      return this.fields.find((field) => field.id === fieldId) || null
    },
    singleSelectFields() {
      return this.fields.filter(
        (field) => field._.type.type === 'single_select'
      )
    },
    cardFields() {
      const fieldOptions =
        this.$store.getters[this.storePrefix + 'view/kanban/getAllFieldOptions']
      // Until the first board response lands there are no options yet, so
      // every field shows in table order; afterwards the visible ones apply
      // in their configured order.
      if (!fieldOptions || Object.keys(fieldOptions).length === 0) {
        return this.fields
      }
      return this.fields
        .filter(filterVisibleFieldsFunction(fieldOptions))
        .sort(sortFieldsByOrderAndIdFunction(fieldOptions))
    },
    canMoveRows() {
      return (
        !this.readOnly &&
        this.$hasPermission(
          'database.table.update_row',
          this.table,
          this.database.workspace.id
        )
      )
    },
  },
  watch: {
    view: {
      handler(view, oldView) {
        // The board depends on the grouping field; a change of view or of
        // the field must reload everything. `immediate` makes this the first
        // load as well.
        if (!oldView || oldView.id !== view.id) {
          this.fetchBoard()
        }
      },
      immediate: true,
    },
  },
  beforeUnmount() {
    this.cancelDrag()
  },
  methods: {
    getStackData(stackId) {
      return this.$store.getters[this.storePrefix + 'view/kanban/getStackData'](
        stackId
      )
    },
    fetchBoard() {
      this.$store
        .dispatch(this.storePrefix + 'view/kanban/fetch', { view: this.view })
        .catch(notifyIf)
    },
    loadMore(stack) {
      this.$store
        .dispatch(this.storePrefix + 'view/kanban/fetchStack', {
          view: this.view,
          stackId: stack.id,
          append: true,
        })
        .catch(notifyIf)
    },
    async selectGroupingField(field) {
      try {
        await this.$client.patch(`/database/views/${this.view.id}/`, {
          single_select_field: field.id,
        })
        this.$store.dispatch('view/forceUpdate', {
          view: this.view,
          values: { single_select_field: field.id },
          registry: this.$registry,
        })
        this.fetchBoard()
      } catch (error) {
        notifyIf(error)
      }
    },
    cardDown(event, row, stack) {
      if (
        event.button !== 0 ||
        !this.canMoveRows ||
        this.getStackData(stack.id).loading
      ) {
        return
      }
      event.preventDefault()

      this.dragState = {
        rowId: row.id,
        row,
        fromStackId: stack.id,
        overStackId: stack.id,
        startX: event.clientX,
        startY: event.clientY,
        moved: false,
      }

      window.addEventListener('mousemove', this.cardMove)
      window.addEventListener('mouseup', this.cardUp)
      document.body.addEventListener('keydown', this.cardEscape)
    },
    cardMove(event) {
      const drag = this.dragState
      if (!drag) {
        return
      }
      if (
        !drag.moved &&
        (Math.abs(event.clientX - drag.startX) > 3 ||
          Math.abs(event.clientY - drag.startY) > 3)
      ) {
        drag.moved = true
      }
      if (!drag.moved) {
        return
      }

      const element = document.elementFromPoint(event.clientX, event.clientY)
      const stackElement = element?.closest('.kanban-view__stack')
      if (stackElement) {
        const stackId = this.stackIdOfElement(stackElement)
        if (stackId !== undefined) {
          drag.overStackId = stackId
        }
      }
    },
    stackIdOfElement(stackElement) {
      for (const stack of this.stacks) {
        const key = `stack-${stack.id}`
        if (this.$refs[key] && this.$refs[key][0] === stackElement) {
          return stack.id
        }
      }
      return undefined
    },
    async cardUp() {
      const drag = this.dragState
      this.cancelDrag()
      if (!drag || !drag.moved || drag.overStackId === drag.fromStackId) {
        return
      }

      try {
        await this.$store.dispatch(this.storePrefix + 'view/kanban/moveRow', {
          table: this.table,
          view: this.view,
          fields: this.fields,
          row: drag.row,
          toStackId: drag.overStackId,
          toStack: this.stacks.find((stack) => stack.id === drag.overStackId),
        })
      } catch (error) {
        notifyIf(error)
      }
    },
    cardEscape(event) {
      if (event.key === 'Escape') {
        this.cancelDrag()
      }
    },
    cancelDrag() {
      window.removeEventListener('mousemove', this.cardMove)
      window.removeEventListener('mouseup', this.cardUp)
      document.body.removeEventListener('keydown', this.cardEscape)
      this.dragState = null
    },
  },
}
</script>
