<template>
  <ThemeConfigBlockSection>
    <template #default>
      <FormGroup
        horizontal-narrow
        small-label
        class="margin-bottom-2"
        :label="$t('pageThemeConfigBlock.backgroundColor')"
      >
        <ColorInput
          v-model="v$.values.page_background_color.$model"
          small
          :allow-opacity="false"
          :color-variables="colorVariables"
        />
      </FormGroup>
      <FormGroup
        horizontal-narrow
        small-label
        class="margin-bottom-2"
        :label="$t('pageThemeConfigBlock.backgroundImage')"
      >
        <ImageInput v-model="v$.values.page_background_file.$model" />
      </FormGroup>
      <FormGroup
        v-if="v$.values.page_background_file.$model"
        horizontal-narrow
        small-label
        class="margin-bottom-2"
        :label="$t('pageThemeConfigBlock.backgroundMode')"
      >
        <RadioGroup
          v-model="v$.values.page_background_mode.$model"
          type="button"
          :options="backgroundModes"
        />
      </FormGroup>
      <FormGroup
        horizontal-narrow
        small-label
        class="margin-bottom-2"
        :label="$t('pageThemeConfigBlock.direction')"
        :helper-text="$t('pageThemeConfigBlock.directionHelp')"
      >
        <RadioGroup
          v-model="v$.values.page_direction.$model"
          type="button"
          :options="directions"
        />
      </FormGroup>
    </template>
  </ThemeConfigBlockSection>
</template>

<script>
import { useVuelidate } from '@vuelidate/core'
import themeConfigBlock from '@jadawel/modules/builder/mixins/themeConfigBlock'
import ThemeConfigBlockSection from '@jadawel/modules/builder/components/theme/ThemeConfigBlockSection'
import { BACKGROUND_MODES } from '@jadawel/modules/builder/enums'

export default {
  name: 'PageThemeConfigBlock',
  components: { ThemeConfigBlockSection },
  mixins: [themeConfigBlock],
  setup() {
    return { v$: useVuelidate() }
  },
  data() {
    return {
      values: {
        page_background_color: this.theme?.page_background_color,
        page_background_file: this.theme?.page_background_file,
        page_background_mode: this.theme?.page_background_mode,
        page_direction: this.theme?.page_direction || 'auto',
      },
    }
  },
  computed: {
    directions() {
      return ['auto', 'rtl', 'ltr'].map((value) => ({
        label: this.$t(`pageThemeConfigBlock.directions.${value}`),
        value,
      }))
    },
    backgroundModes() {
      return [
        {
          label: this.$t('backgroundModes.tile'),
          value: BACKGROUND_MODES.TILE,
        },
        {
          label: this.$t('backgroundModes.fill'),
          value: BACKGROUND_MODES.FILL,
        },
        {
          label: this.$t('backgroundModes.fit'),
          value: BACKGROUND_MODES.FIT,
        },
      ]
    },
  },
  methods: {
    isAllowedKey(key) {
      return key.startsWith('page_')
    },
  },
  validations() {
    return {
      values: {
        page_background_color: {},
        page_background_file: {},
        page_background_mode: {},
        page_direction: {},
      },
    }
  },
}
</script>
