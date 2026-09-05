<template>
  <div class="single-select-color-form">
    <p class="single-select-color-form__help">
      {{ $t('rowColoring.chooseField') }}
    </p>
    <ChooseSingleSelectField
      :table="table"
      :database="database"
      :view="view"
      :fields="fields"
      :read-only="readOnly"
      :value="options.field_id"
      @input="$emit('update', { field_id: $event })"
    />
  </div>
</template>

<script>
import ChooseSingleSelectField from '@jadawel/modules/database/components/field/ChooseSingleSelectField'

export default {
  name: 'SingleSelectColorForm',
  components: { ChooseSingleSelectField },
  props: {
    view: { type: Object, required: true },
    table: { type: Object, required: true },
    database: { type: Object, required: true },
    fields: { type: Array, required: true },
    readOnly: { type: Boolean, required: true },
    options: { type: Object, required: true },
  },
  emits: ['update'],
}
</script>
