import { mountSuspended } from '@nuxt/test-utils/runtime'
import { flushPromises } from '@vue/test-utils'
import { vi } from 'vitest'

import AdminFeatureAccessSettings, {
  parseEmails,
} from '@jadawel/modules/arabase/featureAccess/AdminFeatureAccessSettings'
import { hasFeature } from '@jadawel/modules/arabase/featureAccess/featureAccess'
import { ArabasePlugin } from '@jadawel/modules/arabase/plugins'
import SanadPanel from '@jadawel/modules/arabase/sanad/components/SanadPanel'
import SanadUtilityItem from '@jadawel/modules/arabase/sanad/components/SanadUtilityItem'
import { AutomationApplicationType } from '@jadawel/modules/automation/applicationTypes'
import { BuilderApplicationType } from '@jadawel/modules/builder/applicationTypes'

/**
 * Who sees automations, applications and Sanad (docs/FEATURE_ACCESS.md): the
 * login response carries `arabase_features`, and the admin settings page
 * opens each feature to everyone or to invited email addresses.
 */
const appWith = ({ isStaff = false, features } = {}) => ({
  $store: {
    getters: {
      'auth/isStaff': isStaff,
      'auth/getAdditionalUserData':
        features === undefined ? {} : { arabase_features: features },
    },
  },
})

const NOTHING = { automation: false, builder: false, sanad: false }

describe('what each user sees', () => {
  test('the login response decides, whatever the staff flag says', () => {
    const granted = appWith({ features: { ...NOTHING, builder: true } })
    expect(hasFeature(granted.$store, 'builder')).toBe(true)
    expect(hasFeature(granted.$store, 'automation')).toBe(false)

    // Staff get `true` from the backend; a stale `false` is not overridden.
    const staff = appWith({ isStaff: true, features: NOTHING })
    expect(hasFeature(staff.$store, 'sanad')).toBe(false)
  })

  test('without the login data, staff keep the features as before', () => {
    expect(hasFeature(appWith({ isStaff: true }).$store, 'sanad')).toBe(true)
    expect(hasFeature(appWith().$store, 'sanad')).toBe(false)
  })

  test('creating an automation or an application follows its feature', () => {
    const app = appWith({ features: { ...NOTHING, automation: true } })

    expect(new AutomationApplicationType({ app }).canBeCreated()).toBe(true)
    expect(new BuilderApplicationType({ app }).canBeCreated()).toBe(false)
  })

  test('Sanad opens for a user it is granted to', () => {
    const granted = new ArabasePlugin({
      app: appWith({ features: { ...NOTHING, sanad: true } }),
    })
    const other = new ArabasePlugin({ app: appWith({ features: NOTHING }) })

    expect(granted.getWorkspaceUtilityComponents({})).toEqual([
      SanadUtilityItem,
    ])
    expect(granted.getRightSidebarWorkspaceComponents({})).toEqual([SanadPanel])
    expect(other.getWorkspaceUtilityComponents({})).toEqual([])
    expect(other.getRightSidebarWorkspaceComponents({})).toEqual([])
  })
})

describe('parseEmails', () => {
  test('splits on commas, Arabic commas, semicolons and whitespace', () => {
    expect(
      parseEmails(' a@x.com, b@x.com ،c@x.com;\nd@x.com  a@x.com ,, ')
    ).toEqual(['a@x.com', 'b@x.com', 'c@x.com', 'd@x.com'])
  })
})

describe('AdminFeatureAccessSettings', () => {
  const listing = (overrides = {}) => ({
    data: {
      features: [
        { feature: 'automation', everyone: false, grants: [] },
        {
          feature: 'builder',
          everyone: false,
          grants: [
            {
              id: 5,
              email: 'mona@example.com',
              created_on: '2026-10-03T10:00:00Z',
              user: { id: 9, name: 'Mona', is_staff: false, is_active: true },
            },
            {
              id: 6,
              email: 'invitee@example.com',
              created_on: '2026-10-03T10:00:00Z',
              user: null,
            },
          ],
        },
        { feature: 'sanad', everyone: true, grants: [] },
      ].map((item) => ({ ...item, ...(overrides[item.feature] || {}) })),
    },
  })

  const mountSettings = async (client) => {
    const wrapper = await mountSuspended(AdminFeatureAccessSettings, {
      global: { mocks: { $client: client } },
    })
    await flushPromises()
    return wrapper
  }

  const clientWith = () => ({
    get: vi.fn().mockResolvedValue(listing()),
    patch: vi.fn().mockResolvedValue(listing()),
    post: vi.fn().mockResolvedValue(listing()),
    delete: vi.fn().mockResolvedValue(listing()),
  })

  const featureRow = (wrapper, index) =>
    wrapper.findAll('.feature-access__feature')[index]

  test('lists each feature with its invited users', async () => {
    const client = clientWith()
    const wrapper = await mountSettings(client)

    expect(client.get).toHaveBeenCalledWith('/arabase/admin/feature-access/')
    expect(wrapper.findAll('.feature-access__feature')).toHaveLength(3)

    const builder = featureRow(wrapper, 1)
    const grants = builder.findAll('.feature-access__grant')
    expect(grants).toHaveLength(2)
    expect(grants[0].text()).toContain('mona@example.com')
    expect(grants[0].text()).toContain('Mona')
    // An address without an account is marked, not hidden.
    expect(grants[1].text()).toContain('invitee@example.com')
    expect(grants[1].find('.badge').exists()).toBe(true)

    // A feature open to everyone shows no invite form.
    const sanad = featureRow(wrapper, 2)
    expect(sanad.find('.feature-access__invite').exists()).toBe(false)
    expect(
      featureRow(wrapper, 0).find('.feature-access__invite').exists()
    ).toBe(true)
  })

  test('opening a feature to everyone patches that feature', async () => {
    const client = clientWith()
    client.patch.mockResolvedValue(listing({ automation: { everyone: true } }))
    const wrapper = await mountSettings(client)

    await featureRow(wrapper, 0).find('.switch').trigger('click')
    await flushPromises()

    expect(client.patch).toHaveBeenCalledWith(
      '/arabase/admin/feature-access/automation/',
      { everyone: true }
    )
    expect(
      featureRow(wrapper, 0).find('.feature-access__invite').exists()
    ).toBe(false)
  })

  test('invites the typed addresses and clears the field', async () => {
    const client = clientWith()
    const wrapper = await mountSettings(client)
    const automation = featureRow(wrapper, 0)

    await automation.find('input').setValue('A@example.com, b@example.com')
    await automation.find('form').trigger('submit')
    await flushPromises()

    expect(client.post).toHaveBeenCalledWith(
      '/arabase/admin/feature-access/automation/grants/',
      { emails: ['A@example.com', 'b@example.com'] }
    )
    expect(featureRow(wrapper, 0).find('input').element.value).toBe('')
  })

  test('names an invalid address instead of sending it', async () => {
    const client = clientWith()
    const wrapper = await mountSettings(client)
    const automation = featureRow(wrapper, 0)

    await automation.find('input').setValue('a@example.com, not-an-email')
    await automation.find('form').trigger('submit')
    await flushPromises()

    expect(client.post).not.toHaveBeenCalled()
    const error = featureRow(wrapper, 0).find('.feature-access__error')
    expect(error.exists()).toBe(true)
    expect(featureRow(wrapper, 0).find('input').element.value).toBe(
      'a@example.com, not-an-email'
    )
  })

  test('removes one grant of its own feature', async () => {
    const client = clientWith()
    const wrapper = await mountSettings(client)

    await featureRow(wrapper, 1)
      .findAll('.feature-access__remove')[1]
      .trigger('click')
    await flushPromises()

    expect(client.delete).toHaveBeenCalledWith(
      '/arabase/admin/feature-access/builder/grants/6/'
    )
  })
})
