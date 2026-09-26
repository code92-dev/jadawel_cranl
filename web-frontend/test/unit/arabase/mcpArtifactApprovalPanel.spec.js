import { mountSuspended } from '@nuxt/test-utils/runtime'
import { vi } from 'vitest'
import flushPromises from 'flush-promises'

import McpArtifactApprovalPanel from '@jadawel/modules/arabase/mcp/components/McpArtifactApprovalPanel'

const fetchState = vi.fn()
const approveDraft = vi.fn()

vi.mock('@jadawel/modules/arabase/mcp/services/artifactApproval', () => ({
  default: () => ({ fetchState, approveDraft }),
}))

describe('McpArtifactApprovalPanel', () => {
  beforeEach(() => {
    fetchState.mockReset()
    approveDraft.mockReset()
  })

  test('shows a content-blind approval manifest and view shape', async () => {
    fetchState.mockResolvedValue({
      data: {
        artifact_state: 'pending_approval',
        draft_id: 7,
        endpoint_id: 9,
        view_id: 11,
        audience: 'authenticated',
        manifest: [{ field_id: 41, provenance: 'direct' }],
        view_configuration: {
          row_limit: 25,
          filter_count: 1,
          sort_count: 0,
          group_count: 0,
        },
      },
    })
    const wrapper = await mountSuspended(McpArtifactApprovalPanel, {
      props: {
        view: { id: 11 },
        readOnly: false,
        canUpdate: true,
      },
      global: {
        mocks: {
          $client: {},
          $t: (key, values) =>
            values ? `${key}:${Object.values(values).join(',')}` : key,
        },
      },
    })
    await flushPromises()

    expect(wrapper.text()).toContain('41')
    expect(wrapper.text()).toContain('25')
    expect(wrapper.text()).toContain('9')
    expect(wrapper.text()).not.toContain('protected plaintext')
    expect(wrapper.get('[data-test-id="approve-mcp-artifact"]').exists()).toBe(
      true
    )
  })
})
