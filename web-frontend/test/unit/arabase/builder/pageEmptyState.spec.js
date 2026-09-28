import { mountSuspended } from '@nuxt/test-utils/runtime'
import PageEmptyState from '@jadawel/modules/arabase/builder/components/PageEmptyState.vue'

describe('PageEmptyState', () => {
  const builder = { id: 3 }
  const page = { id: 9, builder_id: 3 }

  const mount = () =>
    mountSuspended(PageEmptyState, {
      props: { page },
      global: { provide: { builder, workspace: {}, dndContext: null } },
    })

  test('opens the gallery and offers quick starts', async () => {
    const wrapper = await mount()

    await wrapper.find('.button').trigger('click')
    expect(wrapper.emitted('add-element')).toHaveLength(1)

    const starts = wrapper.findAll('.page-empty__start')
    expect(starts.length).toBe(5)
  })

  test('a quick start creates the element on the page', async () => {
    const { $store } = useNuxtApp()
    const dispatch = vi.spyOn($store, 'dispatch').mockResolvedValue()
    const wrapper = await mount()

    await wrapper.findAll('.page-empty__start')[0].trigger('click')

    expect(dispatch).toHaveBeenCalledWith('element/create', {
      builder,
      page,
      elementType: 'heading',
    })
    dispatch.mockRestore()
  })
})
