<template>
  <div>
    <form class="margin-bottom-2" @submit.prevent>
      <FormSection :title="$t('textWidgetSettings.content')">
        <FormGroup
          :label="$t('textWidgetSettings.style')"
          class="margin-bottom-2"
          small-label
        >
          <SegmentControl
            :segments="styleSegments"
            :active-index="styleIndex"
            size="small"
            @update:active-index="updateWidget({ text_style: styles[$event] })"
          />
        </FormGroup>
        <FormGroup
          :label="$t('textWidgetSettings.body')"
          :helper-text="$t('textWidgetSettings.bodyHelp')"
          small-label
        >
          <FormTextarea
            v-model="body"
            :min-rows="4"
            :max-rows="12"
            auto-expandable
            :maxlength="2000"
            :placeholder="$t('textWidget.placeholder')"
            @blur="commitBody"
          />
        </FormGroup>
      </FormSection>
    </form>
    <WidgetAppearanceForm
      :widget="widget"
      :store-prefix="storePrefix"
      :features="['icon', 'color']"
      :default-color="widget.text_style === 'callout' ? 'blue' : 'primary'"
    />
  </div>
</template>

<script>
import WidgetAppearanceForm from '@jadawel/modules/arabase/dashboard/components/widget/WidgetAppearanceForm'
import dashboardWidgetSettings from '@jadawel/modules/arabase/dashboard/mixins/dashboardWidgetSettings'

const STYLES = ['section', 'note', 'callout']

export default {
  name: 'TextWidgetSettings',
  components: { WidgetAppearanceForm },
  mixins: [dashboardWidgetSettings],
  data() {
    return {
      // A local copy so typing does not send a request per keystroke.
      body: this.widget.body || '',
    }
  },
  computed: {
    styles() {
      return STYLES
    },
    styleSegments() {
      return [
        { label: this.$t('textWidget.section'), icon: 'iconoir-text' },
        { label: this.$t('textWidget.note'), icon: 'iconoir-page' },
        { label: this.$t('textWidget.callout'), icon: 'iconoir-light-bulb' },
      ]
    },
    styleIndex() {
      return Math.max(0, STYLES.indexOf(this.widget.text_style))
    },
  },
  watch: {
    'widget.id'() {
      this.body = this.widget.body || ''
    },
    'widget.body'(value) {
      // The store rolled a failed update back.
      if (
        value !== this.body &&
        document.activeElement?.tagName !== 'TEXTAREA'
      ) {
        this.body = value || ''
      }
    },
  },
  methods: {
    commitBody() {
      if (this.body !== (this.widget.body || '')) {
        this.updateWidget({ body: this.body })
      }
    },
  },
}
</script>
