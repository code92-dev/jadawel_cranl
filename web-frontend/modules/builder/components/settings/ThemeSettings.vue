<template>
  <div>
    <h2 class="box__title">{{ $t('themeSettings.titleOverview') }}</h2>
    <ThemePresetGallery :builder="builder" @applied="revision++" />
    <ThemeProvider class="theme-settings">
      <Tabs :key="revision">
        <Tab
          v-for="themeConfigBlock in themeConfigBlocks"
          :key="themeConfigBlock.getType()"
          :title="themeConfigBlock.label"
        >
          <div class="padding-top-2">
            <ThemeConfigBlock
              ref="themeConfigBlocks"
              :default-values="builder.theme"
              :theme-config-block-type="themeConfigBlock"
              @values-changed="update($event)"
            />
          </div>
        </Tab>
      </Tabs>
    </ThemeProvider>
  </div>
</template>

<script>
import ThemeProvider from '@jadawel/modules/builder/components/theme/ThemeProvider'
import ThemeConfigBlock from '@jadawel/modules/builder/components/theme/ThemeConfigBlock'
import ThemePresetGallery from '@jadawel/modules/arabase/builder/components/ThemePresetGallery'

import { mapActions } from 'vuex'
import { notifyIf } from '@jadawel/modules/core/utils/error'
import _ from 'lodash'

export default {
  name: 'ThemeSettings',
  components: { ThemeProvider, ThemeConfigBlock, ThemePresetGallery },
  provide() {
    return { builder: this.builder, mode: 'edit' }
  },
  props: {
    builder: {
      type: Object,
      required: true,
    },
  },
  data() {
    // Jadawel fork: bumped when a preset is applied, so the forms below, which
    // copy the theme when they are created, show the new values.
    return { revision: 0 }
  },
  computed: {
    themeConfigBlocks() {
      return this.$registry.getOrderedList('themeConfigBlock')
    },
  },
  methods: {
    ...mapActions({
      setThemeProperty: 'theme/setProperty',
    }),
    async update(newValues) {
      const differences = Object.fromEntries(
        Object.entries(newValues).filter(
          ([key, value]) => !_.isEqual(value, this.builder.theme[key])
        )
      )
      try {
        await Promise.all(
          Object.entries(differences).map(([key, value]) =>
            this.setThemeProperty({ builder: this.builder, key, value })
          )
        )
      } catch (error) {
        this.$refs.themeConfigBlocks.forEach((themeConfigBlock) =>
          themeConfigBlock.reset()
        )
        notifyIf(error, 'application')
      }
    },
  },
}
</script>
