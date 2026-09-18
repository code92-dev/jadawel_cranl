import { mountSuspended } from '@nuxt/test-utils/runtime'

import TableAccessSettings from '@jadawel/modules/arabase/pages/settings/tableAccess'
import { TableAccessWorkspaceSettingsPageType } from '@jadawel/modules/arabase/workspaceSettingsPageTypes'
import {
  GuestRoleTranslationsPermissionManagerType,
  TableGrantsPermissionManagerType,
} from '@jadawel/modules/arabase/permissions'
import { describeApiError } from '@jadawel/modules/arabase/utils/apiError'

const app = { $i18n: { t: (key) => key } }

const workspace = { id: 1 }

const databases = [
  {
    id: 10,
    name: 'CRM',
    type: 'database',
    tables: [
      { id: 100, name: 'Leads' },
      { id: 101, name: 'Salaries' },
    ],
  },
  { id: 11, name: 'Site', type: 'builder' },
]

const mountPage = async (client) =>
  await mountSuspended(TableAccessSettings, {
    props: { workspace },
    global: {
      mocks: {
        $client: client,
        $config: {
          public: { jadawelEmbeddedShareUrl: 'http://localhost:3000' },
        },
        $store: {
          getters: {
            'application/getAllOfWorkspace': () => databases,
          },
        },
      },
    },
  })

const emptyClient = () => ({
  get: vi.fn().mockResolvedValue({ data: { guests: [], invitations: [] } }),
  post: vi.fn().mockResolvedValue({ data: {} }),
  patch: vi.fn().mockResolvedValue({ data: {} }),
  delete: vi.fn().mockResolvedValue({ data: {} }),
})

describe('TableAccessWorkspaceSettingsPageType', () => {
  const page = new TableAccessWorkspaceSettingsPageType({
    app: { ...app, $hasPermission: () => true },
  })

  test('routes to its own settings tab', () => {
    expect(page.getType()).toBe('table-access')
    expect(page.getRoute(workspace)).toEqual({
      name: 'settings-table-access',
      params: { workspaceId: 1 },
    })
  })

  test('is hidden from someone who cannot list invitations', () => {
    const denied = new TableAccessWorkspaceSettingsPageType({
      app: { ...app, $hasPermission: () => false },
    })
    expect(denied.hasPermission(workspace)).toBe(false)
  })
})

describe('GuestRoleTranslationsPermissionManagerType', () => {
  test('labels the GUEST role core would otherwise render undefined', () => {
    const manager = new GuestRoleTranslationsPermissionManagerType({ app })
    expect(manager.getRolesTranslations().GUEST).toEqual({
      name: 'roles.guest.name',
      description: 'roles.guest.description',
    })
  })
})

describe('describeApiError', () => {
  test('flattens a DRF error body into one line', () => {
    expect(
      describeApiError({
        response: { data: { error: 'ERROR_TABLE_NOT_IN_WORKSPACE' } },
      })
    ).toBe('error: ERROR_TABLE_NOT_IN_WORKSPACE')
  })

  test('is quiet when there is no response to describe', () => {
    expect(describeApiError(new Error('network'))).toBe('')
  })
})

describe('Table access settings page', () => {
  test('lists only the tables of database applications', async () => {
    const wrapper = await mountPage(emptyClient())

    expect(wrapper.vm.tables).toEqual([
      { id: 100, name: 'Leads', databaseName: 'CRM' },
      { id: 101, name: 'Salaries', databaseName: 'CRM' },
    ])
  })

  test('sends one entry per selected table with its level', async () => {
    const client = emptyClient()
    const wrapper = await mountPage(client)

    wrapper.vm.form.email = 'guest@example.com'
    wrapper.vm.toggleTable(100)
    wrapper.vm.setLevel(100, 'EDITOR')
    await wrapper.vm.invite()

    expect(client.post).toHaveBeenCalledWith(
      '/arabase/workspace/1/table-access/',
      {
        email: 'guest@example.com',
        tables: [{ table_id: 100, level: 'EDITOR' }],
        base_url: 'http://localhost:3000/workspace-invitation',
      }
    )
  })

  test('deselecting a table drops it from the invitation', async () => {
    const wrapper = await mountPage(emptyClient())

    wrapper.vm.toggleTable(100)
    wrapper.vm.toggleTable(101)
    wrapper.vm.toggleTable(100)

    expect(wrapper.vm.form.tables).toEqual([{ table_id: 101, level: 'VIEWER' }])
  })

  test('surfaces the backend error code instead of swallowing it', async () => {
    const client = emptyClient()
    client.post = vi.fn().mockRejectedValue({
      response: { data: { error: 'ERROR_TABLE_NOT_IN_WORKSPACE' } },
    })
    const wrapper = await mountPage(client)

    wrapper.vm.form.email = 'guest@example.com'
    wrapper.vm.toggleTable(100)
    await wrapper.vm.invite()

    expect(wrapper.vm.error).toBe(true)
    expect(wrapper.vm.errorDetail).toBe('error: ERROR_TABLE_NOT_IN_WORKSPACE')
  })
})

describe('TableGrantsPermissionManagerType', () => {
  const manager = new TableGrantsPermissionManagerType({ app })

  test('says nothing about anyone who is not a guest', () => {
    expect(
      manager.hasPermission({ is_guest: false }, 'database.table.create_field')
    ).toBeUndefined()
  })

  test('hides an operation a guest would be refused anyway', () => {
    expect(
      manager.hasPermission(
        { is_guest: true, table_grants: { 100: 'VIEWER' } },
        'database.table.create_field'
      )
    ).toBe(false)
  })

  test('a viewer guest cannot write rows, an editor guest is left to the backend', () => {
    const viewer = { is_guest: true, table_grants: { 100: 'VIEWER' } }
    const editor = { is_guest: true, table_grants: { 100: 'EDITOR' } }

    expect(manager.hasPermission(viewer, 'database.table.create_row')).toBe(
      false
    )
    expect(
      manager.hasPermission(editor, 'database.table.create_row')
    ).toBeUndefined()
  })

  test('never grants anything on its own', () => {
    const results = [
      manager.hasPermission(
        { is_guest: true, table_grants: { 100: 'VIEWER' } },
        'database.table.list_rows'
      ),
      manager.hasPermission(
        { is_guest: true, table_grants: {} },
        'workspace.read'
      ),
    ]
    expect(results.every((result) => result !== true)).toBe(true)
  })
})
