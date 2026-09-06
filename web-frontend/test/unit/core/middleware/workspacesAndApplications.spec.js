import flushPromises from 'flush-promises'
import middleware from '@jadawel/modules/core/middleware/workspacesAndApplications'
import { TestApp } from '@jadawel/test/helpers/testApp'
import { createWorkspace } from '@jadawel/test/fixtures/workspaces'
import { createApplication } from '@jadawel/test/fixtures/applications'

describe('workspace and application startup', () => {
  let testApp

  beforeEach(() => {
    testApp = new TestApp()
    testApp.store.state.auth.authenticated = true
    testApp.store.state.auth.tokenUpdatedAt = Date.now()
    testApp.store.state.auth.tokenPayload = {
      iat: Date.now() / 1000,
      exp: Date.now() / 1000 + 3600,
    }
    testApp.store.state.auth.user = { completed_onboarding: true }
  })

  afterEach(async () => {
    await testApp.afterEach()
  })

  const run = () => middleware({ params: {}, meta: {} })

  test('starts loading applications while the workspace request is pending', async () => {
    const workspace = createWorkspace(testApp.mock, {})
    const application = createApplication(testApp.mock, {})
    testApp.mockServer.loadPermissions(workspace)
    let releaseWorkspace
    testApp.mock.onGet('/workspaces/').reply(
      () =>
        new Promise((resolve) => {
          releaseWorkspace = () => resolve([200, [workspace]])
        })
    )

    const loading = run()
    await flushPromises()
    const applicationsStarted = testApp.mock.history.get.some(
      (request) => request.url === '/applications/'
    )
    releaseWorkspace()
    await loading

    expect(applicationsStarted).toBe(true)
    expect(testApp.store.getters['workspace/getSelected'].id).toBe(workspace.id)
    expect(testApp.store.getters['application/getAll'][0].id).toBe(
      application.id
    )
  })

  test('waits for workspace permissions even when applications have loaded', async () => {
    const workspace = createWorkspace(testApp.mock, {})
    createApplication(testApp.mock, {})
    let releasePermissions
    testApp.mock.onGet(`/workspaces/${workspace.id}/permissions/`).reply(
      () =>
        new Promise((resolve) => {
          releasePermissions = () => resolve([200, {}])
        })
    )
    let finished = false
    const loading = run().then(() => {
      finished = true
    })
    await flushPromises()
    const finishedBeforePermissions = finished
    releasePermissions()
    await loading
    expect(finishedBeforePermissions).toBe(false)
    expect(testApp.store.getters['workspace/getSelected'].id).toBe(workspace.id)
  })

  test('propagates application loading failures', async () => {
    testApp.mock.onGet('/workspaces/').reply(200, [])
    testApp.mock.onGet('/applications/').reply(500, {})
    await expect(run()).rejects.toMatchObject({ response: { status: 500 } })
    expect(testApp.store.getters['application/isLoaded']).toBe(false)
  })

  test('does not refetch lists on subsequent navigation', async () => {
    const workspace = createWorkspace(testApp.mock, {})
    createApplication(testApp.mock, {})
    testApp.mockServer.loadPermissions(workspace)
    await run()
    testApp.mock.resetHistory()
    await run()
    expect(testApp.mock.history.get).toHaveLength(0)
  })

  test('does not load authenticated data for a signed-out user', async () => {
    testApp.store.state.auth.authenticated = false
    await run()
    expect(testApp.mock.history.get).toHaveLength(0)
  })
})
