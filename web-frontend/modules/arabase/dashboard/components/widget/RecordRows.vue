<template>
  <div class="widget-table">
    <table class="widget-table__table">
      <thead>
        <tr>
          <th
            v-for="field in fields"
            :key="field.id"
            scope="col"
            class="widget-table__head"
            :class="{ 'widget-table__cell--end': alignsEnd(field) }"
          >
            {{ header(field) }}
          </th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="(row, index) in rows"
          :key="row.id ?? index"
          class="widget-table__row"
        >
          <td
            v-for="(field, fieldIndex) in fields"
            :key="field.id"
            class="widget-table__cell"
            :class="{
              'widget-table__cell--first': fieldIndex === 0,
              'widget-table__cell--end': alignsEnd(field),
            }"
            :title="text(row, field)"
          >
            <RecordCell :cell="describe(row, field)" />
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script>
import RecordCell from '@jadawel/modules/arabase/dashboard/components/widget/RecordCell'
import {
  describeRecordValue,
  formatRecordValue,
} from '@jadawel/modules/arabase/dashboard/recordValues'
import { riyalText } from '@jadawel/modules/arabase/dashboard/format'

const END_ALIGNED = ['number', 'count', 'rollup', 'autonumber', 'rating']

/**
 * The rows of a list widget as a compact read-only table. Cells render by field
 * type (`describeRecordValue`): select options keep the colours the grid gives
 * them, numbers line up at the end of the column.
 */
export default {
  name: 'RecordRows',
  components: { RecordCell },
  props: {
    rows: {
      type: Array,
      required: true,
    },
    fields: {
      type: Array,
      required: true,
    },
  },
  methods: {
    describe(row, field) {
      return describeRecordValue(row[field.name], field, this.$i18n.locale)
    },
    text(row, field) {
      return formatRecordValue(row[field.name])
    },
    header(field) {
      return riyalText(field.name)
    },
    alignsEnd(field) {
      return END_ALIGNED.includes(field.type)
    },
  },
}
</script>
