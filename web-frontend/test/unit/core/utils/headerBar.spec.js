import { resolveHeaderBar } from '@jadawel/modules/core/utils/headerBar'

const i18n = { t: (key) => `t(${key})` }
const store = {
  getters: { 'workspace/getSelected': { id: 1, name: 'RCU' } },
}
const registry = {
  getAll: () => ({
    users: {
      routeName: 'admin-users',
      getName: () => 'Users',
      getIconClass: () => 'iconoir-group',
    },
  }),
}

const resolve = (meta, matched = []) =>
  resolveHeaderBar({ route: { meta, matched }, registry, store, i18n })

describe('resolveHeaderBar', () => {
  test('leaves the bar to a page that draws its own', () => {
    expect(resolve({ ownHeader: true, headerTitle: 'x' })).toBeNull()
  })

  test("translates the page's title and keeps its icon", () => {
    expect(
      resolve({ headerTitle: 'sidebar.allWorkspaces', headerIcon: 'i-home' })
    ).toEqual({ title: 't(sidebar.allWorkspaces)', icon: 'i-home' })
  })

  test('calls a title function with the store', () => {
    const headerTitle = ({ store }) =>
      store.getters['workspace/getSelected'].name
    expect(resolve({ headerTitle })).toEqual({ title: 'RCU', icon: null })
  })

  test("takes an admin page's title and icon from its admin type", () => {
    expect(resolve({}, [{ name: 'root' }, { name: 'admin-users' }])).toEqual({
      title: 'Users',
      icon: 'iconoir-group',
    })
  })

  test('still draws an untitled bar on any other page', () => {
    expect(resolve({}, [{ name: 'somewhere' }])).toEqual({
      title: '',
      icon: null,
    })
  })
})
