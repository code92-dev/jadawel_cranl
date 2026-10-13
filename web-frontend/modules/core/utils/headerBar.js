/**
 * Jadawel: what the themed bar across the top of a page shows, or `null` when
 * the page draws its own bar (`definePageMeta({ ownHeader: true })`, as the
 * table, the application editors and My dashboards do).
 *
 * The title is the page's `headerTitle` meta, an i18n key or a function of
 * `{ store, i18n }`, with an optional `headerIcon`. Admin pages need neither:
 * the admin type registered for the route supplies its name and icon, plugins'
 * admin pages included. Any other page still gets the bar, untitled, so the
 * theme colour runs across the top of every page.
 */
export function resolveHeaderBar({ route, registry, store, i18n }) {
  if (route.meta.ownHeader) {
    return null
  }
  const { headerTitle, headerIcon } = route.meta
  if (headerTitle) {
    return {
      title:
        typeof headerTitle === 'function'
          ? headerTitle({ store, i18n }) || ''
          : i18n.t(headerTitle),
      icon: headerIcon || null,
    }
  }
  const adminType = Object.values(registry.getAll('admin')).find((type) =>
    route.matched.some(({ name }) => name === type.routeName)
  )
  if (adminType) {
    return { title: adminType.getName(), icon: adminType.getIconClass() }
  }
  return { title: '', icon: null }
}
