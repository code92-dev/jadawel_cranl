import { mountSuspended } from '@nuxt/test-utils/runtime'
import StepGallery from '@jadawel/modules/arabase/automation/components/StepGallery.vue'
import WorkflowStart from '@jadawel/modules/arabase/automation/components/WorkflowStart.vue'
import WorkflowOverview from '@jadawel/modules/arabase/automation/components/WorkflowOverview.vue'
import { availableRecipes } from '@jadawel/modules/arabase/automation/recipes'

describe('automation editor components', () => {
  test('the start screen offers the recipes and every event', async () => {
    const { $registry } = useNuxtApp()
    const wrapper = await mountSuspended(WorkflowStart)
    const recipes = availableRecipes($registry)
    const triggers = $registry
      .getOrderedList('node')
      .filter((type) => type.isTrigger && type.isEnabled())

    expect(wrapper.findAll('.recipe-card')).toHaveLength(recipes.length)
    expect(wrapper.findAll('.event-card')).toHaveLength(triggers.length)

    await wrapper.find('.recipe-card').trigger('click')
    expect(wrapper.emitted('recipe')[0][0].key).toBe(recipes[0].key)

    await wrapper.find('.event-card').trigger('click')
    expect(wrapper.emitted('add-trigger')[0][0]).toBe(
      'local_jadawel_rows_created'
    )
  })

  test('nothing can be started from a read-only start screen', async () => {
    const wrapper = await mountSuspended(WorkflowStart, {
      props: { readOnly: true },
    })

    expect(
      wrapper.findAll('.recipe-card').every((card) => card.element.disabled)
    ).toBe(true)
  })

  test('the step gallery groups actions and searches their plain names', async () => {
    const { $registry } = useNuxtApp()
    const actions = $registry
      .getOrderedList('node')
      .filter((type) => type.isWorkflowAction)
    const wrapper = await mountSuspended(StepGallery, {
      props: { nodeTypes: actions },
    })

    expect(wrapper.findAll('.step-gallery__section').length).toBeGreaterThan(3)
    // Every category has a jump chip, Messages (where Slack is) among them.
    expect(wrapper.findAll('.step-gallery__jump')).toHaveLength(
      wrapper.findAll('.step-gallery__section').length
    )
    expect(wrapper.text()).toContain(
      wrapper.vm.$t('automationSteps.types.slack_write_message.name')
    )

    await wrapper
      .find('input')
      .setValue(wrapper.vm.$t('automationSteps.types.smtp_email.name'))
    const items = wrapper.findAll('.step-gallery__item')
    expect(items).toHaveLength(1)

    await items[0].trigger('click')
    expect(wrapper.emitted('select')[0][0]).toBe('smtp_email')
  })

  test('the overview counts what is set up and leads to the next step', async () => {
    const node = (id, type, service) => ({ id, type, service })
    const workflow = {
      graph: { 0: 1, 1: { next: { '': [2] } }, 2: {} },
      nodeMap: {
        1: node(1, 'local_jadawel_rows_created', { table_id: 1 }),
        2: node(2, 'smtp_email', {}),
      },
    }
    const { $registry } = useNuxtApp()
    const email = $registry.get('node', 'smtp_email')
    const rows = $registry.get('node', 'local_jadawel_rows_created')
    const emailError = vi.spyOn(email, 'isInError').mockReturnValue(true)
    const rowsError = vi.spyOn(rows, 'isInError').mockReturnValue(false)

    const wrapper = await mountSuspended(WorkflowOverview, {
      props: { workflow, automation: { id: 1 } },
    })

    expect(wrapper.find('.workflow-overview__status').text()).toBe(
      wrapper.vm.$t('workflowOverview.progress', { ready: 1, total: 2 })
    )
    expect(wrapper.findAll('.workflow-overview__step--setup')).toHaveLength(1)
    await wrapper.find('.workflow-overview__next').trigger('click')
    expect(wrapper.emitted('select')[0][0]).toBe(2)

    emailError.mockRestore()
    rowsError.mockRestore()
  })
})
