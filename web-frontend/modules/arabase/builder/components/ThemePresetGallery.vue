<template>
  <section class="theme-presets">
    <div class="theme-presets__head">
      <div>
        <h3 class="theme-presets__title">{{ $t('themePresets.title') }}</h3>
        <p class="theme-presets__subtitle">
          {{ $t('themePresets.subtitle') }}
        </p>
      </div>
      <div class="theme-presets__language">
        <span class="theme-presets__language-label">{{
          $t('themePresets.contentLanguage')
        }}</span>
        <RadioGroup
          v-model="language"
          type="button"
          :options="languageOptions"
        />
      </div>
    </div>
    <div class="theme-presets__grid">
      <button
        v-for="preset in presets"
        :key="preset.key"
        type="button"
        class="theme-preset"
        :class="{ 'theme-preset--active': preset.key === current }"
        :disabled="applying !== null"
        :aria-pressed="preset.key === current"
        @click="apply(preset.key)"
      >
        <span
          class="theme-preset__preview"
          :style="previewStyle(preset)"
          aria-hidden="true"
        >
          <span class="theme-preset__bar">
            <span class="theme-preset__logo"></span>
            <span class="theme-preset__nav"></span>
            <span class="theme-preset__nav"></span>
          </span>
          <span class="theme-preset__body">
            <span class="theme-preset__heading"></span>
            <span class="theme-preset__line"></span>
            <span class="theme-preset__line theme-preset__line--short"></span>
            <span class="theme-preset__actions">
              <span class="theme-preset__button"></span>
              <span class="theme-preset__link"></span>
            </span>
            <span class="theme-preset__table">
              <span class="theme-preset__row theme-preset__row--head"></span>
              <span class="theme-preset__row"></span>
              <span class="theme-preset__row"></span>
            </span>
          </span>
          <span v-if="applying === preset.key" class="theme-preset__loading">
            <span class="loading"></span>
          </span>
        </span>
        <span class="theme-preset__caption">
          <span class="theme-preset__name">
            {{ $t(`themePresets.presets.${preset.key}.name`) }}
            <i
              v-if="preset.key === current"
              class="iconoir-check-circle theme-preset__check"
            ></i>
          </span>
          <span class="theme-preset__description">{{
            $t(`themePresets.presets.${preset.key}.description`)
          }}</span>
        </span>
      </button>
    </div>
    <p v-if="previous" class="theme-presets__applied">
      <i class="iconoir-check"></i>
      {{
        $t('themePresets.applied', {
          name: $t(`themePresets.presets.${previous.key}.name`),
        })
      }}
      <a class="theme-presets__undo" @click="undo">{{
        $t('themePresets.undo')
      }}</a>
    </p>
  </section>
</template>

<script>
import ThemeService from '@jadawel/modules/builder/services/theme'
import { notifyIf } from '@jadawel/modules/core/utils/error'
import {
  THEME_PRESETS,
  contentLanguageOf,
  matchingPreset,
  presetTheme,
} from '@jadawel/modules/arabase/builder/themePresets'

/**
 * The top of an app's Theme settings: complete looks — colours, type scale,
 * buttons, inputs, tables — applied in one click, for Arabic or English
 * content. Every value stays editable in the tabs below; `applied` is emitted
 * so they re-read the theme.
 */
export default {
  name: 'ThemePresetGallery',
  props: {
    builder: {
      type: Object,
      required: true,
    },
  },
  emits: ['applied'],
  data() {
    return {
      language: contentLanguageOf(this.builder.theme, this.$i18n.locale),
      applying: null,
      previous: null,
    }
  },
  computed: {
    presets() {
      return THEME_PRESETS
    },
    current() {
      return matchingPreset(this.builder.theme)
    },
    languageOptions() {
      return [
        { label: this.$t('themePresets.languages.ar'), value: 'ar' },
        { label: this.$t('themePresets.languages.en'), value: 'en' },
      ]
    },
  },
  watch: {
    // Switching the language of an app that is still on a preset re-applies
    // it: the alignments and the direction are what change.
    language() {
      if (this.current && this.applying === null) {
        this.apply(this.current)
      }
    },
  },
  methods: {
    previewStyle(preset) {
      const s = preset.swatches
      return {
        '--preset-page': s.page,
        '--preset-surface': s.surface,
        '--preset-primary': s.primary,
        '--preset-on-primary': s.on_primary,
        '--preset-secondary': s.secondary,
        '--preset-ink': s.ink,
        '--preset-text': s.text,
        '--preset-line': s.line,
        '--preset-subtle': s.subtle,
      }
    },
    async save(values) {
      this.$store.dispatch('theme/forceUpdate', {
        builder: this.builder,
        values,
      })
      await ThemeService(this.$client).update(this.builder.id, values)
    },
    async apply(key) {
      const values = presetTheme(key, this.language)
      const before = Object.fromEntries(
        Object.keys(values).map((name) => [name, this.builder.theme[name]])
      )
      this.applying = key
      try {
        await this.save(values)
        this.previous = { key, values: before }
        this.$emit('applied')
      } catch (error) {
        this.$store.dispatch('theme/forceUpdate', {
          builder: this.builder,
          values: before,
        })
        notifyIf(error, 'application')
      }
      this.applying = null
    },
    async undo() {
      const { values } = this.previous
      this.previous = null
      try {
        await this.save(values)
        this.$emit('applied')
      } catch (error) {
        notifyIf(error, 'application')
      }
    },
  },
}
</script>
