import gridStore from '@jadawel/modules/database/store/view/grid'
import { TestApp } from '@jadawel/test/helpers/testApp'
import {
  EqualViewFilterType,
  ContainsViewFilterType,
} from '@jadawel/modules/database/viewFilters'
import { clone } from '@jadawel/modules/core/utils/object'
import { pathKey } from '@jadawel/modules/database/utils/gridGroupByRender'
import { getDefinedRowsFromSectionRows } from '@jadawel/modules/database/utils/gridGroupBy'
import flushPromises from 'flush-promises'

import { vi } from 'vitest'
import { createStore } from 'vuex'

const groupPathKey = (fieldId, value) =>
  pathKey({ [`field_${fieldId}`]: value }, [{ id: fieldId }])

describe('Grid view store', () => {
  let testApp = null
  let mockServer = null
  let store = null

  beforeEach(() => {
    testApp = new TestApp()
    mockServer = testApp.mockServer
    store = testApp.createStore({
      modules: {
        grid: gridStore,
      },
    })
  })

  afterEach(async () => {
    await testApp.afterEach()
  })

  test('visibleByScrollTop', async () => {
    const state = Object.assign(gridStore.state(), {
      rowPadding: 1,
      bufferStartIndex: 0,
      bufferLimit: 9,
      bufferRequestSize: 3,
      rows: [
        { id: 1, order: '1.00' },
        { id: 2, order: '2.00' },
        { id: 3, order: '3.00' },
        { id: 4, order: '4.00' },
        { id: 5, order: '5.00' },
        { id: 6, order: '6.00' },
        { id: 7, order: '7.00' },
        { id: 8, order: '8.00' },
        { id: 9, order: '9.00' },
      ],
      count: 100,
      windowHeight: 99,
    })

    store.replaceState({ ...store.state, grid: state })

    await store.dispatch('grid/visibleByScrollTop', 0)
    expect(store.getters['grid/getRowsTop']).toBe(0)
    expect(store.getters['grid/getRowsStartIndex']).toBe(0)
    expect(store.getters['grid/getRowsEndIndex']).toBe(3)

    await store.dispatch('grid/visibleByScrollTop', 10)
    expect(store.getters['grid/getRowsTop']).toBe(0)
    expect(store.getters['grid/getRowsStartIndex']).toBe(0)
    expect(store.getters['grid/getRowsEndIndex']).toBe(3)

    await store.dispatch('grid/visibleByScrollTop', 33)
    expect(store.getters['grid/getRowsTop']).toBe(33)
    expect(store.getters['grid/getRowsStartIndex']).toBe(1)
    expect(store.getters['grid/getRowsEndIndex']).toBe(4)

    await store.dispatch('grid/visibleByScrollTop', 66)
    expect(store.getters['grid/getRowsTop']).toBe(66)
    expect(store.getters['grid/getRowsStartIndex']).toBe(2)
    expect(store.getters['grid/getRowsEndIndex']).toBe(5)

    await store.dispatch('grid/visibleByScrollTop', 396)
    expect(store.getters['grid/getRowsTop']).toBe(297)
    expect(store.getters['grid/getRowsStartIndex']).toBe(9)
    expect(store.getters['grid/getRowsEndIndex']).toBe(9)

    store.state.grid.bufferStartIndex = 9
    store.state.grid.rows = [
      { id: 10, order: '10.00' },
      { id: 11, order: '11.00' },
      { id: 12, order: '12.00' },
      { id: 13, order: '13.00' },
      { id: 14, order: '14.00' },
      { id: 15, order: '15.00' },
      { id: 16, order: '16.00' },
      { id: 17, order: '17.00' },
      { id: 18, order: '18.00' },
    ]

    await store.dispatch('grid/visibleByScrollTop', 396)
    expect(store.getters['grid/getRowsTop']).toBe(396)
    expect(store.getters['grid/getRowsStartIndex']).toBe(3)
    expect(store.getters['grid/getRowsEndIndex']).toBe(6)
  })

  test('createdNewRow', async () => {
    const state = Object.assign(gridStore.state(), {
      bufferStartIndex: 0,
      bufferLimit: 6,
      rows: [
        { id: 2, order: '2.00000000000000000000' },
        { id: 3, order: '3.00000000000000000000' },
        { id: 4, order: '4.00000000000000000000' },
        { id: 5, order: '5.00000000000000000000' },
        { id: 6, order: '6.00000000000000000000' },
        { id: 7, order: '7.00000000000000000000' },
      ],
      count: 100,
    })

    store.replaceState({ ...store.state, grid: state })

    const view = {
      filters: [],
      sortings: [],
      ownership_type: 'collaborative',
    }
    const fields = []
    const getScrollTop = () => 0

    await store.dispatch('grid/createdNewRow', {
      view,
      fields,
      values: { id: 1, order: '1.00000000000000000000' },
      getScrollTop,
    })
    expect(store.getters['grid/getAllRows'].length).toBe(7)
    expect(store.getters['grid/getAllRows'][0].id).toBe(1)
    expect(store.getters['grid/getBufferStartIndex']).toBe(0)
    expect(store.getters['grid/getBufferLimit']).toBe(7)
    expect(store.getters['grid/getCount']).toBe(101)

    await store.dispatch('grid/createdNewRow', {
      view,
      fields,
      values: { id: 8, order: '4.50000000000000000000' },
      getScrollTop,
    })
    expect(store.getters['grid/getAllRows'].length).toBe(8)
    expect(store.getters['grid/getAllRows'][0].id).toBe(1)
    expect(store.getters['grid/getAllRows'][4].id).toBe(8)
    expect(store.getters['grid/getBufferStartIndex']).toBe(0)
    expect(store.getters['grid/getBufferLimit']).toBe(8)
    expect(store.getters['grid/getCount']).toBe(102)

    await store.dispatch('grid/createdNewRow', {
      view,
      fields,
      values: { id: 102, order: '102.00000000000000000000' },
      getScrollTop,
    })
    expect(store.getters['grid/getAllRows'].length).toBe(8)
    expect(store.getters['grid/getBufferStartIndex']).toBe(0)
    expect(store.getters['grid/getBufferLimit']).toBe(8)
    expect(store.getters['grid/getCount']).toBe(103)

    store.state.grid.bufferStartIndex = 9
    store.state.grid.bufferLimit = 6
    store.state.grid.rows = [
      { id: 10, order: '10.00000000000000000000' },
      { id: 11, order: '11.00000000000000000000' },
      { id: 12, order: '12.00000000000000000000' },
      { id: 13, order: '13.00000000000000000000' },
      { id: 14, order: '14.00000000000000000000' },
      { id: 15, order: '15.00000000000000000000' },
    ]

    await store.dispatch('grid/createdNewRow', {
      view,
      fields,
      values: { id: 2, order: '2.00000000000000000000' },
      getScrollTop,
    })
    expect(store.getters['grid/getAllRows'].length).toBe(6)
    expect(store.getters['grid/getAllRows'][0].id).toBe(10)
    expect(store.getters['grid/getBufferStartIndex']).toBe(10)
    expect(store.getters['grid/getBufferLimit']).toBe(6)
    expect(store.getters['grid/getCount']).toBe(104)

    // When creating a new row that does not match the filters we don't expect
    // anything to happen because the row does not belong on that view.
    await store.dispatch('grid/createdNewRow', {
      view: {
        id: 1,
        filters_disabled: false,
        filter_type: 'AND',
        filters: [
          {
            id: 1,
            view: 1,
            field: 1,
            type: EqualViewFilterType.getType(),
            value: 'not_matching',
          },
        ],
        sortings: [],
        ownership_type: 'collaborative',
      },
      fields: [
        {
          id: 1,
          name: 'Test 1',
          type: 'text',
          primary: true,
        },
      ],
      values: { id: 16, order: '11.50000000000000000000', field_1: 'value' },
      getScrollTop,
    })
    expect(store.getters['grid/getAllRows'].length).toBe(6)
    expect(store.getters['grid/getAllRows'][0].id).toBe(10)
    expect(store.getters['grid/getAllRows'][1].id).toBe(11)
    expect(store.getters['grid/getAllRows'][2].id).toBe(12)
    expect(store.getters['grid/getAllRows'][3].id).toBe(13)
    expect(store.getters['grid/getAllRows'][4].id).toBe(14)
    expect(store.getters['grid/getAllRows'][5].id).toBe(15)
    expect(store.getters['grid/getBufferStartIndex']).toBe(10)
    expect(store.getters['grid/getBufferLimit']).toBe(6)
    expect(store.getters['grid/getCount']).toBe(104)
  })

  test('updatedExistingRow', async () => {
    const state = Object.assign(gridStore.state(), {
      bufferStartIndex: 0,
      bufferLimit: 3,
      rows: [
        { id: 1, order: '1.00000000000000000000', field_1: 'Value 1' },
        {
          id: 2,
          order: '2.00000000000000000000',
          field_1: 'Value 2',
          _: { mustPersist: true },
        },
        { id: 3, order: '3.00000000000000000000', field_1: 'Value 3' },
      ],
      count: 3,
    })

    store.replaceState({ ...store.state, grid: state })

    const view = {
      id: 1,
      filters_disabled: false,
      filter_type: 'AND',
      filters: [
        {
          id: 1,
          view: 1,
          field: 1,
          type: ContainsViewFilterType.getType(),
          value: 'value',
        },
      ],
      sortings: [],
      ownership_type: 'collaborative',
    }
    const fields = [
      {
        id: 1,
        name: 'Test 1',
        type: 'text',
        primary: true,
      },
    ]
    const getScrollTop = () => 0

    await store.dispatch('grid/updatedExistingRow', {
      view,
      fields,
      row: { id: 2, order: '2.00000000000000000000', field_1: 'Value 2' },
      values: { field_1: 'Value 2 updated' },
      getScrollTop,
    })
    expect(store.getters['grid/getAllRows'].length).toBe(3)
    expect(store.getters['grid/getAllRows'][0].id).toBe(1)
    expect(store.getters['grid/getAllRows'][0].field_1).toBe('Value 1')
    expect(store.getters['grid/getAllRows'][1].id).toBe(2)
    expect(store.getters['grid/getAllRows'][1].field_1).toBe('Value 2 updated')
    expect(store.getters['grid/getAllRows'][1]._.mustPersist).toBe(true)
    expect(store.getters['grid/getAllRows'][2].id).toBe(3)
    expect(store.getters['grid/getAllRows'][2].field_1).toBe('Value 3')
    expect(store.getters['grid/getBufferStartIndex']).toBe(0)
    expect(store.getters['grid/getBufferLimit']).toBe(3)
    expect(store.getters['grid/getCount']).toBe(3)

    await store.dispatch('grid/updatedExistingRow', {
      view,
      fields,
      row: { id: 1, order: '1.00000000000000000000', field_1: 'Value 1' },
      values: { field_1: 'Value 1 updated' },
      getScrollTop,
    })
    expect(store.getters['grid/getAllRows'].length).toBe(3)
    expect(store.getters['grid/getAllRows'][0].id).toBe(1)
    expect(store.getters['grid/getAllRows'][0].field_1).toBe('Value 1 updated')
    expect(store.getters['grid/getAllRows'][1].id).toBe(2)
    expect(store.getters['grid/getAllRows'][1].field_1).toBe('Value 2 updated')
    expect(store.getters['grid/getAllRows'][2].id).toBe(3)
    expect(store.getters['grid/getAllRows'][2].field_1).toBe('Value 3')
    expect(store.getters['grid/getBufferStartIndex']).toBe(0)
    expect(store.getters['grid/getBufferLimit']).toBe(3)
    expect(store.getters['grid/getCount']).toBe(3)

    await store.dispatch('grid/updatedExistingRow', {
      view,
      fields,
      row: { id: 3, order: '3.00000000000000000000', field_1: 'Value 3' },
      values: { field_1: 'Value 3 updated' },
      getScrollTop,
    })
    expect(store.getters['grid/getAllRows'].length).toBe(3)
    expect(store.getters['grid/getAllRows'][0].id).toBe(1)
    expect(store.getters['grid/getAllRows'][0].field_1).toBe('Value 1 updated')
    expect(store.getters['grid/getAllRows'][1].id).toBe(2)
    expect(store.getters['grid/getAllRows'][1].field_1).toBe('Value 2 updated')
    expect(store.getters['grid/getAllRows'][2].id).toBe(3)
    expect(store.getters['grid/getAllRows'][2].field_1).toBe('Value 3 updated')
    expect(store.getters['grid/getBufferStartIndex']).toBe(0)
    expect(store.getters['grid/getBufferLimit']).toBe(3)
    expect(store.getters['grid/getCount']).toBe(3)

    await store.dispatch('grid/updatedExistingRow', {
      view,
      fields,
      row: { id: 4, order: '4.00000000000000000000', field_1: 'empty' },
      values: { field_1: 'Value 4 updated' },
      getScrollTop,
    })
    expect(store.getters['grid/getAllRows'].length).toBe(4)
    expect(store.getters['grid/getAllRows'][0].id).toBe(1)
    expect(store.getters['grid/getAllRows'][0].field_1).toBe('Value 1 updated')
    expect(store.getters['grid/getAllRows'][1].id).toBe(2)
    expect(store.getters['grid/getAllRows'][1].field_1).toBe('Value 2 updated')
    expect(store.getters['grid/getAllRows'][2].id).toBe(3)
    expect(store.getters['grid/getAllRows'][2].field_1).toBe('Value 3 updated')
    expect(store.getters['grid/getAllRows'][3].id).toBe(4)
    expect(store.getters['grid/getAllRows'][3].field_1).toBe('Value 4 updated')
    expect(store.getters['grid/getBufferStartIndex']).toBe(0)
    expect(store.getters['grid/getBufferLimit']).toBe(4)
    expect(store.getters['grid/getCount']).toBe(4)

    await store.dispatch('grid/updatedExistingRow', {
      view,
      fields,
      row: {
        id: 4,
        order: '4.00000000000000000000',
        field_1: 'Value 4 updated',
      },
      values: { field_1: 'empty' },
      getScrollTop,
    })
    expect(store.getters['grid/getAllRows'].length).toBe(3)
    expect(store.getters['grid/getAllRows'][0].id).toBe(1)
    expect(store.getters['grid/getAllRows'][0].field_1).toBe('Value 1 updated')
    expect(store.getters['grid/getAllRows'][1].id).toBe(2)
    expect(store.getters['grid/getAllRows'][1].field_1).toBe('Value 2 updated')
    expect(store.getters['grid/getAllRows'][2].id).toBe(3)
    expect(store.getters['grid/getAllRows'][2].field_1).toBe('Value 3 updated')
    expect(store.getters['grid/getBufferStartIndex']).toBe(0)
    expect(store.getters['grid/getBufferLimit']).toBe(3)
    expect(store.getters['grid/getCount']).toBe(3)

    store.state.grid.bufferStartIndex = 9
    store.state.grid.bufferLimit = 6
    store.state.grid.rows = [
      { id: 10, order: '10.00000000000000000000', field_1: 'Value 10' },
      { id: 11, order: '11.00000000000000000000', field_1: 'Value 11' },
      { id: 12, order: '12.00000000000000000000', field_1: 'Value 12' },
      { id: 13, order: '13.00000000000000000000', field_1: 'Value 13' },
      { id: 14, order: '14.00000000000000000000', field_1: 'Value 14' },
      { id: 15, order: '15.00000000000000000000', field_1: 'Value 15' },
    ]
    store.state.grid.count = 100

    // Change the first row in the buffer. We expect it to be removed from the
    // buffer because aren't 100% sure it still belongs in the buffer.
    await store.dispatch('grid/updatedExistingRow', {
      view,
      fields,
      row: { id: 10, order: '10.00000000000000000000', field_1: 'Value 10' },
      values: { field_1: 'Value 10 updated' },
      getScrollTop,
    })
    expect(store.getters['grid/getAllRows'].length).toBe(5)
    expect(store.getters['grid/getAllRows'][0].id).toBe(11)
    expect(store.getters['grid/getAllRows'][0].field_1).toBe('Value 11')
    expect(store.getters['grid/getAllRows'][1].id).toBe(12)
    expect(store.getters['grid/getAllRows'][1].field_1).toBe('Value 12')
    expect(store.getters['grid/getAllRows'][2].id).toBe(13)
    expect(store.getters['grid/getAllRows'][2].field_1).toBe('Value 13')
    expect(store.getters['grid/getAllRows'][3].id).toBe(14)
    expect(store.getters['grid/getAllRows'][3].field_1).toBe('Value 14')
    expect(store.getters['grid/getAllRows'][4].id).toBe(15)
    expect(store.getters['grid/getAllRows'][4].field_1).toBe('Value 15')
    expect(store.getters['grid/getBufferStartIndex']).toBe(10)
    expect(store.getters['grid/getBufferLimit']).toBe(5)
    expect(store.getters['grid/getCount']).toBe(100)

    // Change the last row in the buffer. We expect it to be deleted from the buffer
    // because it we aren't 100% sure it still belongs in the buffer.
    await store.dispatch('grid/updatedExistingRow', {
      view,
      fields,
      row: { id: 15, order: '15.00000000000000000000', field_1: 'Value 15' },
      values: { field_1: 'Value 15 updated' },
      getScrollTop,
    })
    expect(store.getters['grid/getAllRows'].length).toBe(4)
    expect(store.getters['grid/getAllRows'][0].id).toBe(11)
    expect(store.getters['grid/getAllRows'][0].field_1).toBe('Value 11')
    expect(store.getters['grid/getAllRows'][1].id).toBe(12)
    expect(store.getters['grid/getAllRows'][1].field_1).toBe('Value 12')
    expect(store.getters['grid/getAllRows'][2].id).toBe(13)
    expect(store.getters['grid/getAllRows'][2].field_1).toBe('Value 13')
    expect(store.getters['grid/getAllRows'][3].id).toBe(14)
    expect(store.getters['grid/getAllRows'][3].field_1).toBe('Value 14')
    expect(store.getters['grid/getBufferStartIndex']).toBe(10)
    expect(store.getters['grid/getBufferLimit']).toBe(4)
    expect(store.getters['grid/getCount']).toBe(100)

    // Move a row in the buffer to another position in the buffer.
    await store.dispatch('grid/updatedExistingRow', {
      view,
      fields,
      row: { id: 12, order: '12.00000000000000000000', field_1: 'Value 12' },
      values: {
        order: '13.50000000000000000000',
        field_1: 'Value 13.5',
      },
      getScrollTop,
    })
    expect(store.getters['grid/getAllRows'].length).toBe(4)
    expect(store.getters['grid/getAllRows'][0].id).toBe(11)
    expect(store.getters['grid/getAllRows'][0].field_1).toBe('Value 11')
    expect(store.getters['grid/getAllRows'][1].id).toBe(13)
    expect(store.getters['grid/getAllRows'][1].field_1).toBe('Value 13')
    expect(store.getters['grid/getAllRows'][2].id).toBe(12)
    expect(store.getters['grid/getAllRows'][2].field_1).toBe('Value 13.5')
    expect(store.getters['grid/getAllRows'][3].id).toBe(14)
    expect(store.getters['grid/getAllRows'][3].field_1).toBe('Value 14')
    expect(store.getters['grid/getBufferStartIndex']).toBe(10)
    expect(store.getters['grid/getBufferLimit']).toBe(4)
    expect(store.getters['grid/getCount']).toBe(100)

    // Move an existing row before the buffer. We expect the row to be removed from
    // the buffer because we can't be 100% sure it still belongs in there.
    await store.dispatch('grid/updatedExistingRow', {
      view,
      fields,
      row: {
        id: 12,
        order: '13.50000000000000000000',
        field_1: 'Value 13.5',
      },
      values: {
        order: '2.99999999999999999999',
      },
      getScrollTop,
    })
    expect(store.getters['grid/getAllRows'].length).toBe(3)
    expect(store.getters['grid/getAllRows'][0].id).toBe(11)
    expect(store.getters['grid/getAllRows'][0].field_1).toBe('Value 11')
    expect(store.getters['grid/getAllRows'][1].id).toBe(13)
    expect(store.getters['grid/getAllRows'][1].field_1).toBe('Value 13')
    expect(store.getters['grid/getAllRows'][2].id).toBe(14)
    expect(store.getters['grid/getAllRows'][2].field_1).toBe('Value 14')
    expect(store.getters['grid/getBufferStartIndex']).toBe(11)
    expect(store.getters['grid/getBufferLimit']).toBe(3)
    expect(store.getters['grid/getCount']).toBe(100)

    // Move an existing row before the buffer. We expect the row to be removed from
    // the buffer because we can't be 100% sure it still belongs in there.
    await store.dispatch('grid/updatedExistingRow', {
      view,
      fields,
      row: {
        id: 13,
        order: '13.00000000000000000000',
        field_1: 'Value 13',
      },
      values: {
        order: '16.99999999999999999999',
      },
      getScrollTop,
    })
    expect(store.getters['grid/getAllRows'].length).toBe(2)
    expect(store.getters['grid/getAllRows'][0].id).toBe(11)
    expect(store.getters['grid/getAllRows'][0].field_1).toBe('Value 11')
    expect(store.getters['grid/getAllRows'][1].id).toBe(14)
    expect(store.getters['grid/getAllRows'][1].field_1).toBe('Value 14')
    expect(store.getters['grid/getBufferStartIndex']).toBe(11)
    expect(store.getters['grid/getBufferLimit']).toBe(2)
    expect(store.getters['grid/getCount']).toBe(100)

    // Move a row that is not in the buffer from before to after.
    await store.dispatch('grid/updatedExistingRow', {
      view,
      fields,
      row: {
        id: 2,
        order: '2.00000000000000000000',
        field_1: 'Value 2',
      },
      values: {
        order: '20.99999999999999999999',
        field_2: 'Value 20',
      },
      getScrollTop,
    })
    expect(store.getters['grid/getAllRows'].length).toBe(2)
    expect(store.getters['grid/getAllRows'][0].id).toBe(11)
    expect(store.getters['grid/getAllRows'][0].field_1).toBe('Value 11')
    expect(store.getters['grid/getAllRows'][1].id).toBe(14)
    expect(store.getters['grid/getAllRows'][1].field_1).toBe('Value 14')
    expect(store.getters['grid/getBufferStartIndex']).toBe(10)
    expect(store.getters['grid/getBufferLimit']).toBe(2)
    expect(store.getters['grid/getCount']).toBe(100)

    // Move a row that is not in the buffer from before to after.
    await store.dispatch('grid/updatedExistingRow', {
      view,
      fields,
      row: {
        id: 2,
        order: '20.99999999999999999999',
        field_1: 'Value 20',
      },
      values: {
        order: '2.99999999999999999999',
        field_2: 'Value 20',
      },
      getScrollTop,
    })
    expect(store.getters['grid/getAllRows'].length).toBe(2)
    expect(store.getters['grid/getAllRows'][0].id).toBe(11)
    expect(store.getters['grid/getAllRows'][0].field_1).toBe('Value 11')
    expect(store.getters['grid/getAllRows'][1].id).toBe(14)
    expect(store.getters['grid/getAllRows'][1].field_1).toBe('Value 14')
    expect(store.getters['grid/getBufferStartIndex']).toBe(11)
    expect(store.getters['grid/getBufferLimit']).toBe(2)
    expect(store.getters['grid/getCount']).toBe(100)

    store.state.grid.bufferStartIndex = 9
    store.state.grid.bufferLimit = 6
    store.state.grid.rows = [
      { id: 10, order: '14.99999999999999999995', field_1: 'Value 10' },
      { id: 11, order: '14.99999999999999999996', field_1: 'Value 11' },
      { id: 12, order: '14.99999999999999999997', field_1: 'Value 12' },
      { id: 13, order: '14.99999999999999999998', field_1: 'Value 13' },
      { id: 14, order: '14.99999999999999999999', field_1: 'Value 14' },
      { id: 15, order: '15.00000000000000000000', field_1: 'Value 15' },
    ]
    store.state.grid.count = 100

    // Move the row to an order that already exists, which means all the order lower
    // than the new order should be decreased by 0.00000000000000000001.
    await store.dispatch('grid/updatedExistingRow', {
      view,
      fields,
      row: {
        id: 11,
        order: '14.99999999999999999996',
        field_1: 'Value 11',
      },
      values: {
        order: '14.99999999999999999999',
      },
      getScrollTop,
    })
    expect(store.getters['grid/getAllRows'].length).toBe(6)
    expect(store.getters['grid/getAllRows'][0].id).toBe(10)
    expect(store.getters['grid/getAllRows'][0].order).toBe(
      '14.99999999999999999994'
    )
    expect(store.getters['grid/getAllRows'][1].id).toBe(12)
    expect(store.getters['grid/getAllRows'][1].order).toBe(
      '14.99999999999999999996'
    )
    expect(store.getters['grid/getAllRows'][2].id).toBe(13)
    expect(store.getters['grid/getAllRows'][2].order).toBe(
      '14.99999999999999999997'
    )
    expect(store.getters['grid/getAllRows'][3].id).toBe(14)
    expect(store.getters['grid/getAllRows'][3].order).toBe(
      '14.99999999999999999998'
    )
    expect(store.getters['grid/getAllRows'][4].id).toBe(11)
    expect(store.getters['grid/getAllRows'][4].order).toBe(
      '14.99999999999999999999'
    )
    expect(store.getters['grid/getAllRows'][5].id).toBe(15)
    expect(store.getters['grid/getAllRows'][5].order).toBe(
      '15.00000000000000000000'
    )
    expect(store.getters['grid/getBufferStartIndex']).toBe(9)
    expect(store.getters['grid/getBufferLimit']).toBe(6)
    expect(store.getters['grid/getCount']).toBe(100)

    // If only a field value is updated then there the other row order don't have to be
    // decreased.
    await store.dispatch('grid/updatedExistingRow', {
      view,
      fields,
      row: {
        id: 11,
        order: '14.99999999999999999999',
        field_1: 'Value 11',
      },
      values: {
        field_1: 'Value 11.1',
      },
      getScrollTop,
    })
    expect(store.getters['grid/getAllRows'].length).toBe(6)
    expect(store.getters['grid/getAllRows'][0].id).toBe(10)
    expect(store.getters['grid/getAllRows'][0].order).toBe(
      '14.99999999999999999994'
    )
    expect(store.getters['grid/getAllRows'][1].id).toBe(12)
    expect(store.getters['grid/getAllRows'][1].order).toBe(
      '14.99999999999999999996'
    )
    expect(store.getters['grid/getAllRows'][2].id).toBe(13)
    expect(store.getters['grid/getAllRows'][2].order).toBe(
      '14.99999999999999999997'
    )
    expect(store.getters['grid/getAllRows'][3].id).toBe(14)
    expect(store.getters['grid/getAllRows'][3].order).toBe(
      '14.99999999999999999998'
    )
    expect(store.getters['grid/getAllRows'][4].id).toBe(11)
    expect(store.getters['grid/getAllRows'][4].order).toBe(
      '14.99999999999999999999'
    )
    expect(store.getters['grid/getAllRows'][5].id).toBe(15)
    expect(store.getters['grid/getAllRows'][5].order).toBe(
      '15.00000000000000000000'
    )
    expect(store.getters['grid/getBufferStartIndex']).toBe(9)
    expect(store.getters['grid/getBufferLimit']).toBe(6)
    expect(store.getters['grid/getCount']).toBe(100)
  })

  test('deletedExistingRow', async () => {
    const state = Object.assign(gridStore.state(), {
      bufferStartIndex: 9,
      bufferLimit: 6,
      rows: [
        { id: 10, order: '10.00000000000000000000' },
        { id: 11, order: '11.00000000000000000000' },
        { id: 12, order: '12.00000000000000000000' },
        { id: 13, order: '13.00000000000000000000' },
        { id: 14, order: '14.00000000000000000000' },
        { id: 15, order: '15.00000000000000000000' },
      ],
      count: 100,
    })

    store.replaceState({ ...store.state, grid: state })

    const view = {
      filters: [],
      sortings: [],
      ownership_type: 'collaborative',
    }
    const fields = []
    const getScrollTop = () => 0

    await store.dispatch('grid/deletedExistingRow', {
      view,
      fields,
      row: { id: 3, order: '3.00000000000000000000' },
      getScrollTop,
    })
    expect(store.getters['grid/getAllRows'].length).toBe(6)
    expect(store.getters['grid/getAllRows'][0].id).toBe(10)
    expect(store.getters['grid/getAllRows'][1].id).toBe(11)
    expect(store.getters['grid/getAllRows'][2].id).toBe(12)
    expect(store.getters['grid/getAllRows'][3].id).toBe(13)
    expect(store.getters['grid/getAllRows'][4].id).toBe(14)
    expect(store.getters['grid/getAllRows'][5].id).toBe(15)
    expect(store.getters['grid/getBufferStartIndex']).toBe(8)
    expect(store.getters['grid/getBufferLimit']).toBe(6)
    expect(store.getters['grid/getCount']).toBe(99)

    await store.dispatch('grid/deletedExistingRow', {
      view,
      fields,
      row: { id: 20, order: '20.00000000000000000000' },
      getScrollTop,
    })
    expect(store.getters['grid/getAllRows'].length).toBe(6)
    expect(store.getters['grid/getAllRows'][0].id).toBe(10)
    expect(store.getters['grid/getAllRows'][1].id).toBe(11)
    expect(store.getters['grid/getAllRows'][2].id).toBe(12)
    expect(store.getters['grid/getAllRows'][3].id).toBe(13)
    expect(store.getters['grid/getAllRows'][4].id).toBe(14)
    expect(store.getters['grid/getAllRows'][5].id).toBe(15)
    expect(store.getters['grid/getBufferStartIndex']).toBe(8)
    expect(store.getters['grid/getBufferLimit']).toBe(6)
    expect(store.getters['grid/getCount']).toBe(98)

    await store.dispatch('grid/deletedExistingRow', {
      view,
      fields,
      row: { id: 13, order: '13.00000000000000000000' },
      getScrollTop,
    })
    expect(store.getters['grid/getAllRows'].length).toBe(5)
    expect(store.getters['grid/getAllRows'][0].id).toBe(10)
    expect(store.getters['grid/getAllRows'][1].id).toBe(11)
    expect(store.getters['grid/getAllRows'][2].id).toBe(12)
    expect(store.getters['grid/getAllRows'][3].id).toBe(14)
    expect(store.getters['grid/getAllRows'][4].id).toBe(15)
    expect(store.getters['grid/getBufferStartIndex']).toBe(8)
    expect(store.getters['grid/getBufferLimit']).toBe(5)
    expect(store.getters['grid/getCount']).toBe(97)

    // When deleting a new row that does not match the filters we don't expect
    // anything to happen because the row does not belong on that view.
    await store.dispatch('grid/deletedExistingRow', {
      view: {
        id: 1,
        filters_disabled: false,
        filter_type: 'AND',
        filters: [
          {
            id: 1,
            view: 1,
            field: 1,
            type: EqualViewFilterType.getType(),
            value: 'not_matching',
          },
        ],
        sortings: [],
        ownership_type: 'collaborative',
      },
      fields: [
        {
          id: 1,
          name: 'Test 1',
          type: 'text',
          primary: true,
        },
      ],
      row: { id: 16, order: '11.50000000000000000000', field_1: 'value' },
      getScrollTop,
    })
    expect(store.getters['grid/getAllRows'].length).toBe(5)
    expect(store.getters['grid/getAllRows'][0].id).toBe(10)
    expect(store.getters['grid/getAllRows'][1].id).toBe(11)
    expect(store.getters['grid/getAllRows'][2].id).toBe(12)
    expect(store.getters['grid/getAllRows'][3].id).toBe(14)
    expect(store.getters['grid/getAllRows'][4].id).toBe(15)
    expect(store.getters['grid/getBufferStartIndex']).toBe(8)
    expect(store.getters['grid/getBufferLimit']).toBe(5)
    expect(store.getters['grid/getCount']).toBe(97)
  })
  test('row metadata stored when provided on row create or update', async () => {
    const state = Object.assign(gridStore.state(), {
      bufferStartIndex: 0,
      bufferLimit: 6,
      rows: [{ id: 2, order: '2.00000000000000000000' }],
      count: 1,
    })

    store.replaceState({ ...store.state, grid: state })

    const view = {
      id: 1,
      filters: [],
      sortings: [],
      ownership_type: 'collaborative',
    }
    const fields = []
    const getScrollTop = () => 0

    await store.dispatch('grid/createdNewRow', {
      view,
      fields,
      values: { id: 1, order: '1.00000000000000000000' },
      metadata: { test: 'test' },
      getScrollTop,
    })
    expect(store.getters['grid/getAllRows'].length).toBe(2)
    expect(store.getters['grid/getAllRows'][0].id).toBe(1)
    expect(store.getters['grid/getAllRows'][0]._.metadata.test).toBe('test')

    await store.dispatch('grid/updatedExistingRow', {
      view,
      fields,
      row: { id: 1, order: '1.00000000000000000000' },
      values: { field_1: 'Value updated' },
      metadata: { test: 'test updated' },
      getScrollTop,
    })

    expect(store.getters['grid/getAllRows'].length).toBe(2)
    expect(store.getters['grid/getAllRows'][0].id).toBe(1)
    expect(store.getters['grid/getAllRows'][0]._.metadata.test).toBe(
      'test updated'
    )
  })

  test('fetchAllFieldAggregationData', async () => {
    const state = Object.assign(gridStore.state(), {
      fieldAggregationData: {},
      fieldOptions: {
        2: { aggregation_raw_type: 'empty_count' },
        3: { aggregation_raw_type: 'not_empty_count' },
      },
    })

    store.replaceState({ ...store.state, grid: state })

    const view = {
      id: 1,
    }

    mockServer.getAllFieldAggregationData(view.id, {
      field_2: 84,
      field_3: 256,
    })

    await store.dispatch('grid/fetchAllFieldAggregationData', {
      view,
    })

    expect(clone(store.getters['grid/getAllFieldAggregationData'])).toEqual({
      2: {
        loading: false,
        value: 84,
      },
      3: {
        loading: false,
        value: 256,
      },
    })

    // What if the query fails?
    mockServer.getAllFieldAggregationData(view.id, null, true)

    testApp.dontFailOnErrorResponses()
    await expect(
      store.dispatch('grid/fetchAllFieldAggregationData', {
        view,
      })
    ).rejects.toThrowErrorMatchingSnapshot()
    testApp.failOnErrorResponses()

    expect(clone(store.getters['grid/getAllFieldAggregationData'])).toEqual({
      2: {
        loading: false,
        value: null,
      },
      3: {
        loading: false,
        value: null,
      },
    })
  })

  test('getNumberOfVisibleFields', () => {
    const state = Object.assign(gridStore.state(), {
      fieldOptions: {
        1: {
          order: 0,
          hidden: false,
        },
        2: {
          order: 1,
          hidden: true,
        },
        3: {
          order: 3,
          hidden: false,
        },
        4: {
          order: 2,
          hidden: false,
        },
      },
    })
    const store = createStore({
      modules: {
        grid: {
          ...gridStore,
          state: () => state,
        },
      },
    })

    const nuxtApp = useNuxtApp()

    store.$registry = nuxtApp.$registry

    expect(store.getters['grid/getNumberOfVisibleFields']).toBe(3)
  })

  test('getOrderedFieldOptions', () => {
    const fields = []
    const state = Object.assign(gridStore.state(), {
      fieldOptions: {
        1: {
          order: 0,
          hidden: false,
        },
        2: {
          order: 1,
          hidden: true,
        },
        3: {
          order: 3,
          hidden: false,
        },
        4: {
          order: 2,
          hidden: false,
        },
      },
    })

    store.replaceState({ ...store.state, grid: state })

    expect(
      JSON.parse(
        JSON.stringify(store.getters['grid/getOrderedFieldOptions'](fields))
      )
    ).toEqual([
      [1, { hidden: false, order: 0 }],
      [2, { hidden: true, order: 1 }],
      [4, { hidden: false, order: 2 }],
      [3, { hidden: false, order: 3 }],
    ])
  })

  test('getOrderedFieldOptions places primary field first', () => {
    const fields = [
      { id: 2, primary: false },
      { id: 3, primary: true },
    ]
    const state = Object.assign(gridStore.state(), {
      fieldOptions: {
        1: {
          order: 0,
          hidden: false,
        },
        2: {
          order: 1,
          hidden: true,
        },
        3: {
          order: 3,
          hidden: false,
        },
        4: {
          order: 2,
          hidden: false,
        },
      },
    })

    store.replaceState({ ...store.state, grid: state })

    expect(
      JSON.parse(
        JSON.stringify(store.getters['grid/getOrderedFieldOptions'](fields))
      )
    ).toEqual([
      [3, { hidden: false, order: 3 }],
      [1, { hidden: false, order: 0 }],
      [2, { hidden: true, order: 1 }],
      [4, { hidden: false, order: 2 }],
    ])
  })

  test('getOrderedVisibleFieldOptions', () => {
    const fields = []
    const state = Object.assign(gridStore.state(), {
      fieldOptions: {
        1: {
          order: 0,
          hidden: false,
        },
        2: {
          order: 1,
          hidden: true,
        },
        3: {
          order: 3,
          hidden: false,
        },
        4: {
          order: 2,
          hidden: false,
        },
      },
    })

    store.replaceState({ ...store.state, grid: state })

    expect(
      JSON.parse(
        JSON.stringify(
          store.getters['grid/getOrderedVisibleFieldOptions'](fields)
        )
      )
    ).toEqual([
      [1, { hidden: false, order: 0 }],
      [4, { hidden: false, order: 2 }],
      [3, { hidden: false, order: 3 }],
    ])
  })

  test('getRowIdByIndex', () => {
    const state = Object.assign(gridStore.state(), {
      bufferStartIndex: 9,
      bufferLimit: 10,

      rows: [
        {
          id: 10,
          field_1: '10',
          field_2: 10,
          field_3: true,
          field_4: 'abc',
          order: '10.00',
          _: {},
        },
        {
          id: 11,
          field_1: '11',
          field_2: 11,
          field_3: true,
          field_4: 'def',
          order: '11.00',
          _: {},
        },
      ],
    })

    store.replaceState({ ...store.state, grid: state })

    expect(store.getters['grid/getRowIdByIndex'](10)).toBe(11)
  })

  test('getFieldIdByIndex', () => {
    const fields = []
    const state = Object.assign(gridStore.state(), {
      fieldOptions: {
        1: {
          order: 0,
          hidden: false,
        },
        2: {
          order: 1,
          hidden: true,
        },
        3: {
          order: 3,
          hidden: false,
        },
        4: {
          order: 2,
          hidden: false,
        },
      },
    })

    store.replaceState({ ...store.state, grid: state })

    expect(store.getters['grid/getFieldIdByIndex'](2, fields)).toBe(3)
  })

  test('moveRow reorders inside and across grouped leaf groups', async () => {
    const fields = [
      {
        id: 1,
        name: 'Group',
        type: 'text',
        primary: true,
        _: { type: { type: 'text' } },
      },
    ]
    const groupBys = [{ field: 1, order: 'ASC', type: 'default' }]
    const rowMetadata = {
      selected: true,
      selectedFieldId: -1,
      selectedBy: [],
      loading: false,
      matchFilters: true,
      matchSortings: true,
      matchSearch: true,
      fieldSearchMatches: [],
      persistentId: 'r',
    }
    const fetchAllFieldAggregationData = vi.fn()
    store = testApp.createStore({
      modules: {
        grid: {
          ...gridStore,
          actions: {
            ...gridStore.actions,
            fetchByScrollTopDelayed: vi.fn(),
            fetchAllFieldAggregationData,
          },
        },
        field: {
          namespaced: true,
          getters: { getAll: () => fields },
        },
      },
    })
    const state = Object.assign(gridStore.state(), {
      lastGridId: 1,
      activeGroupBys: groupBys,
      count: 3,
      fieldOptions: {
        1: {
          hidden: false,
          order: 0,
          aggregation_raw_type: 'count',
        },
      },
      groupBy: {
        ...gridStore.state().groupBy,
        treeNodes: [
          { path: { field_1: 'A' }, depth: 0, row_count: 1 },
          { path: { field_1: 'B' }, depth: 0, row_count: 2 },
        ],
        collapse: { mode: 'expand', paths: [] },
      },
    })
    store.replaceState({ ...store.state, grid: state })

    store.commit('grid/SET_GROUP_BY_SECTION_ROWS', {
      sectionKey: groupPathKey(1, 'A'),
      rows: [
        {
          id: 10,
          order: '1.00',
          field_1: 'A',
          _: { ...rowMetadata, persistentId: 'r10' },
        },
      ],
    })
    store.commit('grid/SET_GROUP_BY_SECTION_ROWS', {
      sectionKey: groupPathKey(1, 'B'),
      rows: [
        {
          id: 11,
          order: '2.00',
          field_1: 'B',
          _: { ...rowMetadata, persistentId: 'r11' },
        },
        {
          id: 12,
          order: '3.00',
          field_1: 'B',
          _: { ...rowMetadata, persistentId: 'r12' },
        },
      ],
    })

    mockServer.mock
      .onPatch('/database/rows/table/1/10/')
      .reply(200, { id: 10, order: '1.00', field_1: 'B' })
    mockServer.mock
      .onPatch('/database/rows/table/1/10/move/')
      .reply(200, { id: 10, order: '2.50', field_1: 'B' })

    await store.dispatch('grid/moveRow', {
      table: { id: 1 },
      grid: {
        id: 1,
        filters: [],
        filter_groups: [],
        filter_type: 'AND',
        sortings: [],
        group_bys: groupBys,
      },
      fields,
      getScrollTop: () => 0,
      row: store.getters['grid/getRow'](10),
      before: store.getters['grid/getRow'](12),
      sourceGroupPath: { field_1: 'A' },
      targetGroupPath: { field_1: 'B' },
    })

    const updateRequest = mockServer.mock.history.patch[0]
    const moveRequest = mockServer.mock.history.patch[1]
    expect(JSON.parse(updateRequest.data)).toEqual({ field_1: 'B' })
    expect(updateRequest.params).toMatchObject({ view: 1 })
    expect(JSON.parse(moveRequest.data)).toBeNull()
    expect(moveRequest.params).toMatchObject({ before_id: 12, view: 1 })
    expect(updateRequest.headers.ClientUndoRedoActionGroupId).toBeTruthy()
    expect(moveRequest.headers.ClientUndoRedoActionGroupId).toBe(
      updateRequest.headers.ClientUndoRedoActionGroupId
    )
    expect(
      getDefinedRowsFromSectionRows(
        store.state.grid.groupBy.sectionRows,
        groupPathKey(1, 'B')
      ).map((row) => row.id)
    ).toEqual([11, 10, 12])
    expect(store.getters['grid/getRow'](10)).toMatchObject({
      field_1: 'B',
      order: '2.50',
    })
    expect(store.state.grid.groupBy.treeNodes[0].row_count).toBe(0)
    expect(store.state.grid.groupBy.treeNodes[1].row_count).toBe(3)
    expect(fetchAllFieldAggregationData).toHaveBeenLastCalledWith(
      expect.anything(),
      expect.objectContaining({ clearGroupByAggregationLoadingPaths: true })
    )

    mockServer.mock
      .onPatch('/database/rows/table/1/12/move/')
      .reply(200, { id: 12, order: '1.50', field_1: 'B' })

    await store.dispatch('grid/moveRow', {
      table: { id: 1 },
      grid: {
        id: 1,
        filters: [],
        filter_groups: [],
        filter_type: 'AND',
        sortings: [],
        group_bys: groupBys,
      },
      fields,
      getScrollTop: () => 0,
      row: store.getters['grid/getRow'](12),
      before: store.getters['grid/getRow'](11),
      sourceGroupPath: { field_1: 'B' },
      targetGroupPath: { field_1: 'B' },
    })

    const sameGroupRequest = mockServer.mock.history.patch[2]
    expect(JSON.parse(sameGroupRequest.data)).toBeNull()
    expect(sameGroupRequest.params).toMatchObject({ before_id: 11, view: 1 })
    expect(sameGroupRequest.headers.ClientUndoRedoActionGroupId).toBeUndefined()
    expect(
      getDefinedRowsFromSectionRows(
        store.state.grid.groupBy.sectionRows,
        groupPathKey(1, 'B')
      ).map((row) => row.id)
    ).toEqual([12, 11, 10])
    expect(store.state.grid.groupBy.treeNodes[1].row_count).toBe(3)
    expect(fetchAllFieldAggregationData).toHaveBeenLastCalledWith(
      expect.anything(),
      expect.objectContaining({ clearGroupByAggregationLoadingPaths: false })
    )

    mockServer.mock
      .onPatch('/database/rows/table/1/11/')
      .reply(200, { id: 11, order: '2.00', field_1: 'A' })
    mockServer.mock.onPatch('/database/rows/table/1/11/move/').reply(500)
    testApp.dontFailOnErrorResponses()

    await expect(
      store.dispatch('grid/moveRow', {
        table: { id: 1 },
        grid: {
          id: 1,
          filters: [],
          filter_groups: [],
          filter_type: 'AND',
          sortings: [],
          group_bys: groupBys,
        },
        fields,
        getScrollTop: () => 0,
        row: store.getters['grid/getRow'](11),
        sourceGroupPath: { field_1: 'B' },
        targetGroupPath: { field_1: 'A' },
      })
    ).rejects.toThrow()

    const partialUpdateRequest = mockServer.mock.history.patch[3]
    const failedMoveRequest = mockServer.mock.history.patch[4]
    expect(failedMoveRequest.headers.ClientUndoRedoActionGroupId).toBe(
      partialUpdateRequest.headers.ClientUndoRedoActionGroupId
    )
    expect(
      getDefinedRowsFromSectionRows(
        store.state.grid.groupBy.sectionRows,
        groupPathKey(1, 'A')
      ).map((row) => row.id)
    ).toEqual([11])
    expect(store.getters['grid/getRow'](11)).toMatchObject({
      field_1: 'A',
      order: '2.00',
    })
    expect(store.state.grid.groupBy.treeNodes[0].row_count).toBe(1)
    expect(store.state.grid.groupBy.treeNodes[1].row_count).toBe(2)
    expect(fetchAllFieldAggregationData).toHaveBeenLastCalledWith(
      expect.anything(),
      expect.objectContaining({ clearGroupByAggregationLoadingPaths: true })
    )

    // When the first request fails, the optimistic group move is rolled back and
    // no aggregation refresh follows. The rollback must finish before its loading
    // paths are cleared, otherwise it can leave the group banners spinning forever.
    store.commit('grid/SET_GROUP_BY_AGGREGATIONS_LOADING_PATHS', [])
    mockServer.mock.onPatch('/database/rows/table/1/12/').reply(500)

    await expect(
      store.dispatch('grid/moveRow', {
        table: { id: 1 },
        grid: {
          id: 1,
          filters: [],
          filter_groups: [],
          filter_type: 'AND',
          sortings: [],
          group_bys: groupBys,
        },
        fields,
        getScrollTop: () => 0,
        row: store.getters['grid/getRow'](12),
        before: store.getters['grid/getRow'](11),
        sourceGroupPath: { field_1: 'B' },
        targetGroupPath: { field_1: 'A' },
      })
    ).rejects.toThrow()
    await flushPromises()

    expect(
      getDefinedRowsFromSectionRows(
        store.state.grid.groupBy.sectionRows,
        groupPathKey(1, 'A')
      ).map((row) => row.id)
    ).toEqual([11])
    expect(
      getDefinedRowsFromSectionRows(
        store.state.grid.groupBy.sectionRows,
        groupPathKey(1, 'B')
      ).map((row) => row.id)
    ).toEqual([12, 10])
    expect(store.state.grid.groupBy.aggregationsLoadingPaths).toEqual([])
  })

  test('moveRow immediately applies the destination group display value', async () => {
    const optionA = { id: 101, value: 'A', color: 'blue' }
    const optionB = { id: 102, value: 'B', color: 'green' }
    const fields = [
      {
        id: 1,
        name: 'Name',
        type: 'text',
        primary: true,
        _: { type: { type: 'text' } },
      },
      {
        id: 2,
        name: 'Group',
        type: 'single_select',
        primary: false,
        select_options: [optionA, optionB],
        _: { type: { type: 'single_select' } },
      },
    ]
    const groupBys = [{ field: 2, order: 'ASC', type: 'default' }]
    const rowMetadata = {
      selected: false,
      selectedFieldId: -1,
      selectedBy: [],
      loading: false,
      matchFilters: true,
      matchSortings: true,
      matchSearch: true,
      fieldSearchMatches: [],
      persistentId: 'r',
    }
    store = testApp.createStore({
      modules: {
        grid: {
          ...gridStore,
          actions: {
            ...gridStore.actions,
            fetchByScrollTopDelayed: vi.fn(),
            fetchAllFieldAggregationData: vi.fn(),
          },
        },
        field: {
          namespaced: true,
          getters: { getAll: () => fields },
        },
      },
    })
    const state = Object.assign(gridStore.state(), {
      lastGridId: 1,
      activeGroupBys: groupBys,
      count: 2,
      fieldOptions: {
        1: { hidden: false, order: 0 },
        2: { hidden: false, order: 1 },
      },
      groupBy: {
        ...gridStore.state().groupBy,
        treeNodes: [
          {
            path: { field_2: optionA.id },
            display: { field_2: optionA },
            depth: 0,
            row_count: 1,
          },
          {
            path: { field_2: optionB.id },
            display: { field_2: optionB },
            depth: 0,
            row_count: 1,
          },
        ],
        collapse: { mode: 'expand', paths: [] },
      },
    })
    store.replaceState({ ...store.state, grid: state })
    store.commit('grid/SET_GROUP_BY_SECTION_ROWS', {
      sectionKey: groupPathKey(2, optionA.id),
      rows: [
        {
          id: 10,
          order: '1.00',
          field_1: 'Alice',
          field_2: optionA,
          _: { ...rowMetadata, persistentId: 'r10' },
        },
      ],
    })
    store.commit('grid/SET_GROUP_BY_SECTION_ROWS', {
      sectionKey: groupPathKey(2, optionB.id),
      rows: [
        {
          id: 11,
          order: '2.00',
          field_1: 'Bob',
          field_2: optionB,
          _: { ...rowMetadata, persistentId: 'r11' },
        },
      ],
    })

    let finishUpdate
    mockServer.mock.onPatch('/database/rows/table/1/10/').reply(
      () =>
        new Promise((resolve) => {
          finishUpdate = () =>
            resolve([
              200,
              {
                id: 10,
                order: '1.00',
                field_1: 'Alice',
                field_2: optionB,
              },
            ])
        })
    )
    mockServer.mock.onPatch('/database/rows/table/1/10/move/').reply(200, {
      id: 10,
      order: '1.50',
      field_1: 'Alice',
      field_2: optionB,
    })

    const movePromise = store.dispatch('grid/moveRow', {
      table: { id: 1 },
      grid: {
        id: 1,
        filters: [],
        filter_groups: [],
        filter_type: 'AND',
        sortings: [],
        group_bys: groupBys,
      },
      fields,
      getScrollTop: () => 0,
      row: store.getters['grid/getRow'](10),
      before: store.getters['grid/getRow'](11),
      sourceGroupPath: { field_2: optionA.id },
      targetGroupPath: { field_2: optionB.id },
      targetGroupDisplay: { field_2: optionB },
    })

    await vi.waitFor(() => expect(finishUpdate).toBeTypeOf('function'))
    const optimisticValue = store.getters['grid/getRow'](10).field_2
    finishUpdate()
    await movePromise

    expect(optimisticValue).toEqual(optionB)
    expect(JSON.parse(mockServer.mock.history.patch[0].data)).toEqual({
      field_2: optionB.id,
    })
  })

  test('updatedExistingRow moves a selected formula-group row without a placeholder', async () => {
    const fields = [
      { id: 1, name: 'Name', type: 'text', primary: true },
      {
        id: 2,
        name: 'Computed team',
        type: 'formula',
        formula_type: 'text',
        read_only: true,
      },
    ]
    const groupBys = [{ field: 2, order: 'ASC', type: 'default' }]
    const rowMetadata = {
      selected: false,
      selectedFieldId: -1,
      selectedBy: [],
      loading: false,
      matchFilters: true,
      matchSortings: true,
      matchSearch: true,
      fieldSearchMatches: [],
      persistentId: 'r',
    }
    const state = Object.assign(gridStore.state(), {
      activeGroupBys: groupBys,
      count: 2,
      fieldOptions: {
        1: { hidden: false, order: 0 },
        2: { hidden: false, order: 1 },
      },
      groupBy: {
        ...gridStore.state().groupBy,
        treeNodes: [
          { path: { field_2: 'A' }, depth: 0, row_count: 1 },
          { path: { field_2: 'B' }, depth: 0, row_count: 1 },
        ],
        collapse: { mode: 'expand', paths: [] },
      },
    })

    store.replaceState({ ...store.state, grid: state })
    store.commit('grid/SET_GROUP_BY_SECTION_ROWS', {
      sectionKey: groupPathKey(2, 'A'),
      rows: [
        {
          id: 10,
          order: '1.00',
          field_1: 'Alice',
          field_2: 'A',
          _: {
            ...rowMetadata,
            persistentId: 'r10',
            selected: true,
            selectedFieldId: 1,
            selectedBy: [1],
          },
        },
      ],
    })
    store.commit('grid/SET_GROUP_BY_SECTION_ROWS', {
      sectionKey: groupPathKey(2, 'B'),
      rows: [
        {
          id: 11,
          order: '2.00',
          field_1: 'Bob',
          field_2: 'B',
          _: { ...rowMetadata, persistentId: 'r11' },
        },
      ],
    })

    await store.dispatch('grid/updatedExistingRow', {
      view: {
        filters: [],
        filter_groups: [],
        filter_type: 'AND',
        sortings: [],
        group_bys: groupBys,
      },
      fields,
      row: store.getters['grid/getRow'](10),
      values: { field_2: 'B' },
      updatedFieldIds: [2],
    })

    expect(
      store.state.grid.groupBy.sectionRows[groupPathKey(2, 'A')].map(
        (row) => row.id
      )
    ).toEqual([])
    expect(
      store.state.grid.groupBy.sectionRows[groupPathKey(2, 'B')].map(
        (row) => row.id
      )
    ).toEqual([10, 11])
    expect(store.getters['grid/getRow'](10)._.matchSortings).toBe(true)
    expect(store.state.grid.groupBy.treeNodes).toEqual([
      { path: { field_2: 'A' }, depth: 0, row_count: 0 },
      { path: { field_2: 'B' }, depth: 0, row_count: 2 },
    ])
  })
})

describe('Grid view store group-by layout mode', () => {
  let testApp = null
  let store = null

  const fields = [
    { id: 1, name: 'Name', type: 'text', primary: true },
    { id: 2, name: 'Team', type: 'text' },
  ]
  const groupBys = [
    { id: 10, field: 2, order: 'ASC', type: 'default', width: 200 },
  ]
  const view = {
    id: 1,
    filters: [],
    filter_groups: [],
    filter_type: 'AND',
    sortings: [],
    group_bys: groupBys,
  }
  const seed = (targetStore, extra = {}) => {
    const state = Object.assign(gridStore.state(), {
      lastGridId: 1,
      activeGroupBys: groupBys,
      rowHeight: 33,
      windowHeight: 100,
      fieldOptions: {
        1: { hidden: false, order: 0 },
        2: { hidden: false, order: 1 },
      },
      groupBy: {
        ...gridStore.state().groupBy,
        treeNodes: [{ path: { field_2: 'A' }, depth: 0, row_count: 2 }],
        collapse: { mode: 'expand', paths: [] },
      },
      ...extra,
    })
    targetStore.replaceState({ ...targetStore.state, grid: state })
  }

  beforeEach(() => {
    testApp = new TestApp()
    store = testApp.createStore({ modules: { grid: gridStore } })
  })

  afterEach(async () => {
    await testApp.afterEach()
  })

  test('setGroupByLayout switches the layout builder and forces expand-all', async () => {
    seed(store)
    store.commit('grid/SET_GROUP_BY_COLLAPSE', { mode: 'collapse', paths: [] })
    expect(
      store.getters['grid/getGroupByLayout'].items.map((item) => item.type)
    ).toEqual(['header'])

    await store.dispatch('grid/setGroupByLayout', 'column')

    expect(store.getters['grid/isGroupByColumnLayout']).toBe(true)
    expect(
      store.getters['grid/getGroupByLayout'].items.map((item) => item.type)
    ).toEqual(['groupSpan', 'rowSection', 'addRow'])
  })

  test('collapse actions are no-ops in column layout', async () => {
    const fetchGroupByRowsByScrollTop = vi.fn().mockResolvedValue([])
    const groupByStore = testApp.createStore({
      modules: {
        grid: {
          ...gridStore,
          actions: { ...gridStore.actions, fetchGroupByRowsByScrollTop },
        },
      },
    })
    seed(groupByStore, { groupByLayout: 'column' })

    await groupByStore.dispatch('grid/toggleGroupCollapse', {
      path: { field_2: 'A' },
      view,
      fields,
    })
    await groupByStore.dispatch('grid/setGroupByCollapseAll', {
      view,
      fields,
      collapse: true,
    })

    expect(groupByStore.getters['grid/getGroupByCollapse']).toEqual({
      mode: 'expand',
      paths: [],
    })
    expect(fetchGroupByRowsByScrollTop).not.toHaveBeenCalled()
  })

  test.each(['column', 'section'])(
    '%s layout selects loaded rows beyond an unloaded group page',
    async (layout) => {
      const nodes = Object.fromEntries(
        [0, 80].flatMap((offset) =>
          Array.from({ length: 40 }, (_, index) => {
            const position = offset + index
            return [
              position,
              {
                path: { field_2: `Group ${position}` },
                depth: 0,
                row_count: 1,
                sibling_index: position,
                row_offset: position,
              },
            ]
          })
        )
      )
      seed(store, {
        groupByLayout: layout,
        count: 120,
        groupBy: {
          ...gridStore.state().groupBy,
          pages: { '': { parentPath: {}, totalSiblingCount: 120, nodes } },
        },
      })
      for (const rowId of [100, 101]) {
        store.commit('grid/SET_GROUP_BY_SECTION_ROWS', {
          sectionKey: groupPathKey(2, `Group ${rowId}`),
          startPosition: 0,
          rows: [
            {
              id: rowId,
              field_2: `Group ${rowId}`,
              _: { selected: false, selectedFieldId: -1 },
            },
          ],
        })
      }

      await store.dispatch('grid/multiSelectStart', {
        rowId: 100,
        fieldIndex: 0,
      })
      await store.dispatch('grid/multiSelectHold', {
        rowId: 101,
        fieldIndex: 1,
      })

      const firstRowIndex = layout === 'column' ? 100 : 60
      expect(store.getters['grid/getMultiSelectRowIndexSorted']).toEqual([
        firstRowIndex,
        firstRowIndex + 1,
      ])
      expect(
        store.getters['grid/getSelectedRows'].map((row) => row.id)
      ).toEqual([100, 101])

      await store.dispatch('grid/correctMultiSelect')

      expect(store.getters['grid/getMultiSelectRowIndexSorted']).toEqual([
        firstRowIndex,
        firstRowIndex + 1,
      ])
      expect(
        store.getters['grid/getSelectedRows'].map((row) => row.id)
      ).toEqual([100, 101])

      await store.dispatch('grid/updateMultipleSelectIndexes', {
        position: 'tail',
        rowIndex: layout === 'column' ? 120 : 80,
        fieldIndex: 1,
      })
      expect(store.getters['grid/getMultiSelectRowIndexSorted']).toEqual([
        firstRowIndex,
        firstRowIndex + 1,
      ])
    }
  )

  test('column layout initially fetches descendants despite a saved collapse-all state', async () => {
    const nestedFields = [
      { id: 1, name: 'Name', type: 'text', primary: true },
      { id: 2, name: 'Team', type: 'text' },
      { id: 3, name: 'Role', type: 'text' },
    ]
    const nestedGroupBys = [
      { field: 2, order: 'ASC', type: 'default', width: 200 },
      { field: 3, order: 'ASC', type: 'default', width: 200 },
    ]
    const nestedView = { ...view, group_bys: nestedGroupBys }
    const state = Object.assign(gridStore.state(), {
      lastGridId: 1,
      activeGroupBys: nestedGroupBys,
      groupByLayout: 'column',
      count: 2,
      rowHeight: 33,
      rowPadding: 0,
      windowHeight: 330,
      fieldOptions: {
        1: { hidden: false, order: 0 },
        2: { hidden: false, order: 1 },
        3: { hidden: false, order: 2 },
      },
      groupBy: {
        ...gridStore.state().groupBy,
        pages: {},
        treeNodes: [],
        collapse: { mode: 'collapse', paths: [] },
        collapseInitialized: true,
      },
    })
    store.replaceState({ ...store.state, grid: state })

    const groupByRequests = []
    testApp.mockServer.mock
      .onGet('/database/views/grid/1/group-by-data/')
      .reply((config) => {
        groupByRequests.push(config.params)
        return [
          200,
          {
            pages: [
              {
                parent: {},
                groups: [
                  {
                    path: { field_2: 'A' },
                    depth: 0,
                    row_count: 2,
                    children_count: 1,
                    sibling_index: 0,
                    row_offset: 0,
                  },
                ],
                offset: 0,
                limit: 40,
                group_count: 1,
              },
              {
                parent: { field_2: 'A' },
                groups: [
                  {
                    path: { field_2: 'A', field_3: 'Dev' },
                    depth: 1,
                    row_count: 2,
                    sibling_index: 0,
                    row_offset: 0,
                  },
                ],
                offset: 0,
                limit: 40,
                group_count: 1,
              },
            ],
          },
        ]
      })
    testApp.mockServer.mock.onGet('/database/views/grid/1/').reply(200, {
      count: 2,
      results: [
        {
          id: 10,
          order: '1.00',
          field_1: 'Alice',
          field_2: 'A',
          field_3: 'Dev',
        },
        { id: 11, order: '2.00', field_1: 'Ada', field_2: 'A', field_3: 'Dev' },
      ],
    })

    await store.dispatch('grid/fetchGroupByRowsByScrollTop', {
      gridId: 1,
      view: nestedView,
      fields: nestedFields,
      scrollTop: 0,
    })

    expect(groupByRequests).toHaveLength(1)
    expect(groupByRequests[0].get('include_descendants')).toBe('true')
    expect(groupByRequests[0].get('depth')).toBe(null)
    expect(store.state.grid.groupBy.collapse).toEqual({
      mode: 'collapse',
      paths: [],
    })
  })

  test('column viewport refines sparse group pages until rows are visible', async () => {
    const sparseGroupBys = [
      { id: 10, field: 2, order: 'ASC', type: 'default', width: 200 },
    ]
    const sparseView = { ...view, group_bys: sparseGroupBys }
    const state = Object.assign(gridStore.state(), {
      lastGridId: 1,
      activeGroupBys: sparseGroupBys,
      groupByLayout: 'column',
      count: 12000,
      bufferRequestSize: 40,
      rowHeight: 33,
      rowPadding: 0,
      windowHeight: 33,
      fieldOptions: {
        1: { hidden: false, order: 0 },
        2: { hidden: false, order: 1 },
      },
      groupBy: {
        ...gridStore.state().groupBy,
        pages: {
          '': {
            parentPath: {},
            totalSiblingCount: 120,
            nodes: {},
          },
        },
        collapse: { mode: 'expand', paths: [] },
        collapseInitialized: true,
      },
    })
    store.replaceState({ ...store.state, grid: state })

    const groupPageOffsets = []
    testApp.mockServer.mock
      .onGet('/database/views/grid/1/group-by-data/')
      .reply((config) => {
        const [{ offset }] = JSON.parse(config.params.get('parents'))
        groupPageOffsets.push(offset)
        const isLastPage = offset === 80
        const rowCount = isLastPage ? 1 : 100
        const rowOffset = isLastPage ? 11960 : 7960
        return [
          200,
          {
            pages: [
              {
                parent: {},
                groups: Array.from({ length: 40 }, (_, index) => ({
                  path: { field_2: `Group ${offset + index}` },
                  depth: 0,
                  row_count: rowCount,
                  sibling_index: offset + index,
                  row_offset: rowOffset + index * rowCount,
                })),
                offset,
                limit: 40,
                group_count: 120,
              },
            ],
          },
        ]
      })

    const rowRequests = []
    testApp.mockServer.mock.onGet('/database/views/grid/1/').reply((config) => {
      rowRequests.push(config.params)
      return [
        200,
        {
          count: 12000,
          results: [
            {
              id: 8001,
              order: '8001.00',
              field_1: 'Visible row',
              field_2: 'Group 40',
            },
          ],
        },
      ]
    })

    await store.dispatch('grid/fetchGroupByRowsByScrollTop', {
      gridId: 1,
      view: sparseView,
      fields,
      scrollTop: 8000 * 33,
    })

    // Loading the initially visible final page changes the estimated heights of the
    // earlier sparse pages. The same viewport then falls in page 40 and must be refined
    // again before row ranges can be resolved.
    expect(groupPageOffsets).toEqual([80, 40])
    expect(rowRequests).toHaveLength(1)
    expect(rowRequests[0].get('offset')).toBe('7960')
  })

  test('column layout refresh uses expanded paging but preserves section collapse state', async () => {
    const nestedFields = [
      { id: 1, name: 'Name', type: 'text', primary: true },
      { id: 2, name: 'Team', type: 'text' },
      { id: 3, name: 'Role', type: 'text' },
    ]
    const nestedGroupBys = [
      { field: 2, order: 'ASC', type: 'default', width: 200 },
      { field: 3, order: 'ASC', type: 'default', width: 200 },
    ]
    const nestedView = { ...view, group_bys: nestedGroupBys }
    const state = Object.assign(gridStore.state(), {
      lastGridId: 1,
      activeGroupBys: nestedGroupBys,
      groupByLayout: 'column',
      count: 2,
      rowHeight: 33,
      rowPadding: 0,
      windowHeight: 330,
      fieldOptions: {
        1: { hidden: false, order: 0 },
        2: { hidden: false, order: 1 },
        3: { hidden: false, order: 2 },
      },
      groupBy: {
        ...gridStore.state().groupBy,
        collapse: { mode: 'collapse', paths: [] },
        collapseInitialized: true,
      },
    })
    store.replaceState({ ...store.state, grid: state })

    const rootPage = {
      parent: {},
      groups: [
        {
          path: { field_2: 'A' },
          depth: 0,
          row_count: 2,
          children_count: 1,
          sibling_index: 0,
          row_offset: 0,
        },
      ],
      offset: 0,
      limit: 40,
      group_count: 1,
    }
    const childPage = {
      parent: { field_2: 'A' },
      groups: [
        {
          path: { field_2: 'A', field_3: 'Dev' },
          depth: 1,
          row_count: 2,
          sibling_index: 0,
          row_offset: 0,
        },
      ],
      offset: 0,
      limit: 40,
      group_count: 1,
    }
    const groupByRequests = []
    testApp.mockServer.mock
      .onGet('/database/views/grid/1/group-by-data/')
      .reply((config) => {
        groupByRequests.push(config.params)
        const pages =
          config.params.get('include_descendants') === 'true'
            ? [rootPage, childPage]
            : config.params.get('depth') !== null
              ? [childPage]
              : [rootPage]
        return [200, { pages }]
      })
    testApp.mockServer.mock.onGet('/database/views/grid/1/').reply(200, {
      count: 2,
      results: [
        {
          id: 10,
          order: '1.00',
          field_1: 'Alice',
          field_2: 'A',
          field_3: 'Dev',
        },
        { id: 11, order: '2.00', field_1: 'Ada', field_2: 'A', field_3: 'Dev' },
      ],
    })

    await store.dispatch('grid/refreshActiveGroupBys', {
      view: nestedView,
      fields: nestedFields,
      scrollTop: 0,
      preserveScroll: true,
    })

    expect(groupByRequests).toHaveLength(1)
    expect(groupByRequests[0].get('include_descendants')).toBe('true')
    expect(groupByRequests[0].get('depth')).toBe(null)
    expect(store.state.grid.groupBy.collapse).toEqual({
      mode: 'collapse',
      paths: [],
    })
  })
})
