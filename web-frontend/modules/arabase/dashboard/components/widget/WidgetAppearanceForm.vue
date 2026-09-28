<template>
  <form class="widget-appearance-form" @submit.prevent>
    <FormSection :title="$t('widgetAppearance.title')">
      <slot></slot>

      <FormGroup
        v-if="features.includes('color')"
        :label="$t('widgetAppearance.color')"
        class="margin-bottom-2"
        small-label
      >
        <div class="widget-appearance-form__swatches" role="radiogroup">
          <button
            v-for="color in colors"
            :key="color"
            type="button"
            role="radio"
            class="widget-appearance-form__swatch"
            :class="[
              `widget-accent--${color}`,
              {
                'widget-appearance-form__swatch--active':
                  color === currentColor,
              },
            ]"
            :aria-checked="color === currentColor ? 'true' : 'false'"
            :title="$t(`widgetAppearance.colors.${color}`)"
            :aria-label="$t(`widgetAppearance.colors.${color}`)"
            @click="set({ color })"
          ></button>
        </div>
      </FormGroup>

      <FormGroup
        v-if="features.includes('icon')"
        :label="$t('widgetAppearance.icon')"
        class="margin-bottom-2"
        small-label
      >
        <div class="widget-appearance-form__icons" role="radiogroup">
          <button
            type="button"
            role="radio"
            class="widget-appearance-form__icon"
            :class="{
              'widget-appearance-form__icon--active': currentIcon === null,
            }"
            :aria-checked="currentIcon === null ? 'true' : 'false'"
            :title="$t('widgetAppearance.noIcon')"
            :aria-label="$t('widgetAppearance.noIcon')"
            @click="set({ icon: null })"
          >
            <i class="iconoir-prohibition"></i>
          </button>
          <button
            v-for="icon in icons"
            :key="icon"
            type="button"
            role="radio"
            class="widget-appearance-form__icon"
            :class="{
              'widget-appearance-form__icon--active': icon === currentIcon,
            }"
            :aria-checked="icon === currentIcon ? 'true' : 'false'"
            :title="icon"
            :aria-label="icon"
            @click="set({ icon })"
          >
            <i :class="`iconoir-${icon}`"></i>
          </button>
        </div>
      </FormGroup>

      <template v-if="features.includes('number')">
        <div class="widget-appearance-form__affixes margin-bottom-2">
          <FormGroup :label="$t('widgetAppearance.prefix')" small-label>
            <FormInput
              v-model="prefix"
              size="small"
              :placeholder="$t('widgetAppearance.prefixPlaceholder')"
              @blur="commitAffixes"
              @keydown.enter.prevent="commitAffixes"
            />
          </FormGroup>
          <FormGroup :label="$t('widgetAppearance.suffix')" small-label>
            <FormInput
              v-model="suffix"
              size="small"
              :placeholder="$t('widgetAppearance.suffixPlaceholder')"
              @blur="commitAffixes"
              @keydown.enter.prevent="commitAffixes"
            />
          </FormGroup>
        </div>
        <FormGroup
          :label="$t('widgetAppearance.decimals')"
          class="margin-bottom-2"
          small-label
          horizontal
          horizontal-narrow
        >
          <Dropdown
            :model-value="currentDecimals"
            @update:model-value="
              set({ decimals: $event === 'auto' ? null : $event })
            "
          >
            <DropdownItem
              :name="$t('widgetAppearance.decimalsAuto')"
              value="auto"
            ></DropdownItem>
            <DropdownItem
              v-for="decimals in [0, 1, 2, 3, 4]"
              :key="decimals"
              :name="decimalsExample(decimals)"
              :value="decimals"
            ></DropdownItem>
          </Dropdown>
        </FormGroup>
        <FormGroup small-label class="margin-bottom-2">
          <Checkbox
            :model-value="appearance.compact === true"
            @update:model-value="set({ compact: $event })"
            >{{ $t('widgetAppearance.compact') }}</Checkbox
          >
        </FormGroup>
      </template>

      <FormGroup v-if="features.includes('stacked')" small-label>
        <Checkbox
          :model-value="appearance.stacked === true"
          @update:model-value="set({ stacked: $event })"
          >{{ $t('widgetAppearance.stacked') }}</Checkbox
        >
      </FormGroup>
    </FormSection>
  </form>
</template>

<script>
import {
  ACCENT_COLORS,
  ICONS,
  accentOf,
  appearanceOf,
  iconOf,
} from '@jadawel/modules/arabase/dashboard/appearance'
import { formatNumber } from '@jadawel/modules/arabase/dashboard/format'
import { notifyIf } from '@jadawel/modules/core/utils/error'

/**
 * The "Appearance" section of a widget's settings: accent colour, icon, number
 * format and chart stacking, each shown only where the widget uses it
 * (`features`). Type-specific display options go in the default slot so each
 * widget has one place for how it looks.
 *
 * Every change writes the whole `appearance` dict — it is one field on the
 * widget, and a partial write would drop the other options.
 */
export default {
  name: 'WidgetAppearanceForm',
  props: {
    widget: {
      type: Object,
      required: true,
    },
    storePrefix: {
      type: String,
      required: false,
      default: '',
    },
    features: {
      type: Array,
      required: false,
      default: () => ['color', 'icon'],
    },
    defaultColor: {
      type: String,
      required: false,
      default: 'primary',
    },
  },
  data() {
    return {
      prefix: appearanceOf(this.widget).prefix || '',
      suffix: appearanceOf(this.widget).suffix || '',
    }
  },
  computed: {
    appearance() {
      return appearanceOf(this.widget)
    },
    colors() {
      return ACCENT_COLORS
    },
    icons() {
      return ICONS
    },
    currentColor() {
      return accentOf(this.widget, this.defaultColor)
    },
    currentIcon() {
      return iconOf(this.widget)
    },
    currentDecimals() {
      return Number.isInteger(this.appearance.decimals)
        ? this.appearance.decimals
        : 'auto'
    },
  },
  watch: {
    'widget.id'() {
      this.prefix = this.appearance.prefix || ''
      this.suffix = this.appearance.suffix || ''
    },
  },
  methods: {
    decimalsExample(decimals) {
      return formatNumber(1234.5678, {
        decimals,
        locale: this.$i18n.locale,
      })
    },
    commitAffixes() {
      const prefix = this.prefix.trim()
      const suffix = this.suffix.trim()
      if (
        prefix !== (this.appearance.prefix || '') ||
        suffix !== (this.appearance.suffix || '')
      ) {
        this.set({ prefix: prefix || null, suffix: suffix || null })
      }
    },
    async set(changes) {
      const next = { ...this.appearance, ...changes }
      // Unset options are dropped rather than stored as null, keeping the dict
      // to what was actually chosen.
      Object.keys(next).forEach((key) => {
        if (next[key] === null || next[key] === false || next[key] === '') {
          delete next[key]
        }
      })
      try {
        await this.$store.dispatch(
          `${this.storePrefix}dashboardApplication/updateWidget`,
          {
            widgetId: this.widget.id,
            values: { appearance: next },
            originalValues: { appearance: this.widget.appearance || {} },
          }
        )
      } catch (error) {
        notifyIf(error, 'dashboard')
      }
    },
  },
}
</script>
