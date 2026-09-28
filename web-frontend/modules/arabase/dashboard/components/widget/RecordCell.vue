<template>
  <span v-if="cell.kind === 'pills'" class="widget-table__pills">
    <span
      v-for="(item, i) in cell.items"
      :key="i"
      class="widget-pill"
      :class="`background-color--${item.color}`"
      >{{ item.text }}</span
    >
  </span>
  <span v-else-if="cell.kind === 'chips'" class="widget-table__pills">
    <span v-for="(item, i) in cell.items" :key="i" class="widget-chip">{{
      item.text
    }}</span>
  </span>
  <span v-else-if="cell.kind === 'people'" class="widget-table__pills">
    <span v-for="(item, i) in cell.items" :key="i" class="widget-person">
      <span class="widget-person__avatar" aria-hidden="true">{{
        item.initial
      }}</span>
      {{ item.text }}
    </span>
  </span>
  <i
    v-else-if="cell.kind === 'boolean'"
    :class="
      cell.value
        ? 'iconoir-check widget-table__check'
        : 'iconoir-minus widget-table__uncheck'
    "
    :aria-label="cell.value ? '✓' : '—'"
  ></i>
  <span
    v-else-if="cell.kind === 'rating'"
    class="widget-table__rating"
    :aria-label="`${cell.value} / ${cell.max}`"
    >{{ '★'.repeat(Math.max(0, Math.min(cell.max, cell.value)))
    }}<span class="widget-table__rating-rest">{{
      '★'.repeat(Math.max(0, cell.max - cell.value))
    }}</span></span
  >
  <span v-else-if="cell.kind === 'empty'" class="widget-table__empty">—</span>
  <span
    v-else
    :class="{ 'widget-table__number': cell.kind === 'number' }"
    dir="auto"
    >{{ cell.text }}</span
  >
</template>

<script>
/**
 * One cell of a list widget, drawn from what `describeRecordValue` made of it.
 */
export default {
  name: 'RecordCell',
  props: {
    cell: {
      type: Object,
      required: true,
    },
  },
}
</script>
