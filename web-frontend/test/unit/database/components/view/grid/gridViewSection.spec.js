import { nextTick } from 'vue'

import { TestApp } from '@jadawel/test/helpers/testApp'
import GridViewSection from '@jadawel/modules/database/components/view/grid/GridViewSection'

describe('GridViewSection component', () => {
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
    type: 'text',
    primary: index === 0,
  }))

  const mountSection = (groupBys = []) =>
    testApp.mount(GridViewSection, {
      props: {
        visibleFields: fields,
        allVisibleFields: fields,
        allFieldsInTable: fields,
        decorationsByPlace: {},
        database: { id: 1, workspace: { id: 1 } },
        table: { id: 1, data_sync: null },
        view: {
          id: 1,
          group_bys: groupBys,
          row_identifier_type: 'id',
          filters_disabled: false,
          filters: [],
          sortings: [],
        },
        readOnly: true,
        storePrefix: 'page/',
      },
      global: {
        stubs: {
          HorizontalResize: true,
          GridViewHead: true,
          GridViewPlaceholder: true,
          GridViewGroupByRows: {
            props: ['renderedFields', 'leftOffset'],
            template:
              '<div class="test-grid-grouped-row" :data-left-offset="leftOffset"></div>',
          },
          GridViewRowAdd: true,
          GridViewFieldFooter: true,
          GridViewRows: {
            props: ['renderedFields', 'leftOffset'],
            template: `
              <div class="test-grid-row" :data-left-offset="leftOffset">
                <div
                  v-for="field in renderedFields"
                  :key="field.id"
                  class="test-grid-cell"
                  :data-field-id="field.id"
                />
              </div>
            `,
          },
        },
      },
    })

  test('renders fields at a negative RTL scroll offset', async () => {
    await testApp.store.dispatch(
      'page/view/grid/forceUpdateAllFieldOptions',
      Object.fromEntries(
        fields.map((field) => [field.id, { width: 200, hidden: false }])
      )
    )

    const wrapper = await mountSection()

    Object.defineProperties(wrapper.element, {
      clientWidth: { configurable: true, value: 1127 },
      scrollWidth: { configurable: true, value: 1600 },
      scrollLeft: { configurable: true, value: -437 },
    })
    wrapper.element.style.direction = 'rtl'

    await wrapper.trigger('scroll')
    await new Promise((resolve) => setTimeout(resolve, 60))
    await nextTick()

    expect(
      wrapper
        .findAll('.test-grid-cell')
        .map((cell) => Number(cell.attributes('data-field-id')))
    ).toEqual([2, 3, 4, 5, 6, 7, 8])
    expect(wrapper.find('.test-grid-row').attributes('data-left-offset')).toBe(
      '-200'
    )
  })

  test('renders the grouped canvas instead of flat rows when grouping', async () => {
    await testApp.store.dispatch(
      'page/view/grid/forceUpdateAllFieldOptions',
      Object.fromEntries(
        fields.map((field) => [field.id, { width: 200, hidden: false }])
      )
    )
    await testApp.store.dispatch('page/view/grid/updateActiveGroupBys', [
      { id: 1, field: 2, order: 'ASC', type: 'default', width: 200 },
    ])

    const wrapper = await mountSection([
      { id: 1, field: 2, order: 'ASC', type: 'default', width: 200 },
    ])

    expect(wrapper.vm.useGroupByRows).toBe(true)
    expect(wrapper.find('.test-grid-grouped-row').exists()).toBe(true)
    expect(wrapper.find('.test-grid-row').exists()).toBe(false)
    // The flat add-row button is replaced by the per-group add rows.
    expect(wrapper.find('.grid-view__row-add').exists()).toBe(false)
  })
})
