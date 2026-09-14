import { nextTick } from 'vue'

import { TestApp } from '@jadawel/test/helpers/testApp'
import ViewGroupByContext from '@jadawel/modules/database/components/view/ViewGroupByContext'

describe('ViewGroupByContext component', () => {
  let testApp = null

  beforeEach(() => {
    testApp = new TestApp()
  })

  afterEach(async () => {
    await testApp.afterEach()
  })

  const fields = Array.from({ length: 8 }, (_, index) => ({
    id: index + 1,
    name: `Field ${index + 1}`,
    order: index,
    type: 'text',
    primary: index === 0,
    text_default: '',
    _: { loading: false },
  }))

  const groupBys = (count) =>
    fields.slice(0, count).map((field) => ({
      id: `group-by-${field.id}`,
      field: field.id,
      order: 'ASC',
      type: 'default',
      width: 200,
      _: { loading: false },
    }))

  const mountContext = async (groupByCount) => {
    const wrapper = await testApp.mount(ViewGroupByContext, {
      props: {
        database: { id: 1, workspace: { id: 1 } },
        fields,
        view: {
          id: 1,
          group_bys: groupBys(groupByCount),
          ownership_type: 'collaborative',
        },
        readOnly: false,
        disableGroupBy: false,
      },
    })
    // The Context only renders its slot after it has been opened once.
    wrapper.vm.$refs.context.forceRender()
    await nextTick()
    return wrapper
  }

  test('offers the add button while below the group by limit', async () => {
    const wrapper = await mountContext(4)

    const addButton = wrapper.find('.group-bys__footer button')
    expect(addButton.exists()).toBe(true)
    expect(addButton.attributes('disabled')).toBeUndefined()
  })

  test('refuses a sixth group by and disables the add button', async () => {
    const wrapper = await mountContext(5)

    const addButton = wrapper.find('.group-bys__footer button')
    expect(addButton.exists()).toBe(true)
    expect(addButton.attributes('disabled')).toBeDefined()

    // The wrapping span's tooltip explains why the button is disabled.
    const tooltip = wrapper.find('.group-bys__footer > span')
    expect(tooltip.element.tooltipOptions.value).toMatch(
      /^viewGroupByContext\.maxGroupBysReached/
    )

    // The 6th field is not offered in the dropdown either.
    expect(wrapper.vm.availableFields.map((field) => field.id)).toEqual([
      6, 7, 8,
    ])
    expect(wrapper.vm.atGroupByLimit).toBe(true)
  })
})
