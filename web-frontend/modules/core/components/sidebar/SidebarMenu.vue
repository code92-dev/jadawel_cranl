<template>
  <div class="sidebar__section" ph-autocapture="sidebar" data-highlight="menu">
    <!--
      Jadawel: the workspace utilities that used to live here — notifications,
      members, invite, trash — moved to the top inline-end corner of the content
      area as icon buttons (see AppUtilities). What stays is navigation: the
      places you go to and remain.
    -->
    <ul class="tree">
      <nuxt-link
        v-slot="{ href, navigate, isExactActive }"
        custom
        :to="{
          name: 'workspace',
          params: {
            workspaceId: selectedWorkspace.id,
          },
        }"
      >
        <li
          class="tree__item"
          :class="{
            active: isExactActive,
          }"
        >
          <div class="tree__action sidebar__action">
            <a :href="href" class="tree__link" @click="navigate">
              <i class="tree__icon iconoir-clock"></i>
              <span class="tree__link-text">
                <span class="sidebar__item-name">{{
                  $t('sidebar.recents')
                }}</span>
              </span>
            </a>
          </div>
        </li>
      </nuxt-link>

      <component
        :is="component"
        v-for="(component, index) in sidebarWorkspaceComponents"
        :key="'sidebarWorkspaceComponents' + index"
        :workspace="selectedWorkspace"
        :right-sidebar-open="rightSidebarOpen"
      ></component>
    </ul>
  </div>
</template>

<script>
export default {
  name: 'SidebarMenu',
  props: {
    selectedWorkspace: {
      type: Object,
      required: true,
    },
    rightSidebarOpen: {
      type: Boolean,
      required: false,
      default: false,
    },
  },
  computed: {
    sidebarWorkspaceComponents() {
      return Object.values(this.$registry.getAll('plugin'))
        .flatMap((plugin) =>
          plugin.getSidebarWorkspaceComponents(this.selectedWorkspace)
        )
        .filter((component) => component !== null)
    },
  },
}
</script>
