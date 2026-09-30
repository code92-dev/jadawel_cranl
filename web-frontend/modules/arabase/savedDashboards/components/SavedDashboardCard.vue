<template>
  <div
    class="saved-dashboard-card"
    :class="{ 'saved-dashboard-card--blocked': !isOpenable }"
  >
    <button
      type="button"
      class="saved-dashboard-card__preview"
      :aria-label="$t('myDashboards.open', { name: title })"
      @click="primaryAction"
    >
      <div v-if="card.preview.length" class="saved-dashboard-card__sketch">
        <span
          v-for="(widget, index) in card.preview"
          :key="index"
          class="saved-dashboard-card__block"
          :class="`saved-dashboard-card__block--${blockKind(widget.type)}`"
          :style="blockStyle(widget)"
        ></span>
      </div>
      <i v-else class="saved-dashboard-card__empty jadawel-icon-dashboard"></i>

      <span
        v-if="card.status !== 'ok'"
        class="saved-dashboard-card__status"
        :class="`saved-dashboard-card__status--${card.status}`"
      >
        <i :class="statusIcon"></i>
        {{ $t(`myDashboards.status.${card.status}`) }}
      </span>
    </button>

    <div class="saved-dashboard-card__footer">
      <div class="saved-dashboard-card__text">
        <div class="saved-dashboard-card__title" :title="title">
          {{ title }}
        </div>
        <div class="saved-dashboard-card__source">
          <i :class="sourceIcon"></i>
          <span>{{ sourceLabel }}</span>
        </div>
      </div>
      <a
        ref="menuLink"
        class="saved-dashboard-card__menu"
        :aria-label="$t('myDashboards.menu')"
        @click.stop="$refs.menu.toggle($refs.menuLink, 'bottom', 'right', 4)"
      >
        <i class="iconoir-more-vert"></i>
      </a>
    </div>

    <Context ref="menu" overflow-scroll max-height-if-outside-viewport>
      <ul class="context__menu">
        <li v-if="isOpenable" class="context__menu-item">
          <a class="context__menu-item-link" @click="menuAction('open')">
            <i class="context__menu-item-icon iconoir-open-new-window"></i>
            {{ $t('myDashboards.openAction') }}
          </a>
        </li>
        <li
          v-if="card.source === 'workspace' && card.status === 'ok'"
          class="context__menu-item"
        >
          <a
            class="context__menu-item-link"
            @click="menuAction('open-in-workspace')"
          >
            <i class="context__menu-item-icon jadawel-icon-dashboard"></i>
            {{ $t('myDashboards.openInWorkspace') }}
          </a>
        </li>
        <li v-if="card.status === 'password'" class="context__menu-item">
          <a class="context__menu-item-link" @click="menuAction('password')">
            <i class="context__menu-item-icon iconoir-lock"></i>
            {{ $t('myDashboards.enterPassword') }}
          </a>
        </li>
        <li class="context__menu-item context__menu-item--with-separator">
          <a
            class="context__menu-item-link context__menu-item-link--delete"
            @click="menuAction('remove')"
          >
            <i class="context__menu-item-icon iconoir-trash"></i>
            {{ $t('myDashboards.remove') }}
          </a>
        </li>
      </ul>
    </Context>
  </div>
</template>

<script>
// The widget types that draw a chart or a list, so the sketch reads like the
// dashboard it stands for; anything else is a plain block.
const BLOCK_KINDS = {
  summary: 'number',
  progress: 'number',
  chart: 'chart',
  records_list: 'list',
  upcoming_dates: 'list',
  text: 'text',
}

/**
 * One saved dashboard on "My dashboards": a sketch of its layout (no data, so
 * the gallery loads nothing per card), its name, where it comes from, and why
 * it cannot be opened when it cannot.
 */
export default {
  name: 'SavedDashboardCard',
  props: {
    card: {
      type: Object,
      required: true,
    },
  },
  emits: ['open', 'open-in-workspace', 'password', 'remove'],
  computed: {
    title() {
      return this.card.title || this.$t('myDashboards.untitled')
    },
    isOpenable() {
      return this.card.status === 'ok' || this.card.status === 'unreachable'
    },
    sourceIcon() {
      return {
        workspace: 'iconoir-view-grid',
        link: 'iconoir-link',
        remote: 'iconoir-cloud-sync',
      }[this.card.source]
    },
    sourceLabel() {
      return this.card.source === 'link'
        ? this.$t('myDashboards.sharedLink')
        : this.card.source_name
    },
    statusIcon() {
      return {
        password: 'iconoir-lock',
        unavailable: 'iconoir-warning-triangle',
        unreachable: 'iconoir-cloud-sync',
      }[this.card.status]
    },
  },
  methods: {
    blockKind(type) {
      return BLOCK_KINDS[type] || 'plain'
    },
    blockStyle(widget) {
      const width = Math.min(12, Math.max(1, parseInt(widget.width) || 12))
      const height = Math.min(12, Math.max(1, parseInt(widget.height) || 4))
      return { gridColumn: `span ${width}`, gridRow: `span ${height}` }
    },
    primaryAction() {
      if (this.card.status === 'password') {
        this.$emit('password', this.card)
      } else if (this.isOpenable) {
        this.$emit('open', this.card)
      }
    },
    menuAction(action) {
      this.$refs.menu.hide()
      this.$emit(action, this.card)
    },
  },
}
</script>
