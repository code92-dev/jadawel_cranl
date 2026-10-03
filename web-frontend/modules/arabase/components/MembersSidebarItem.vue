<template>
  <nuxt-link
    v-slot="{ href, navigate, isExactActive }"
    custom
    :to="{ name: 'arabase-workspace-members' }"
  >
    <li class="tree__item" :class="{ active: isExactActive }">
      <div class="tree__action sidebar__action">
        <a :href="href" class="tree__link" @click="navigate">
          <i class="tree__icon iconoir-group"></i>
          <span class="tree__link-text">
            <span class="sidebar__item-name">{{
              $t('workspaceMembers.title')
            }}</span>
          </span>
        </a>
      </div>
    </li>
  </nuxt-link>
</template>

<script>
/** The workspaces sidebar's way to the members of every workspace. */
export default {
  name: 'MembersSidebarItem',
}
</script>
