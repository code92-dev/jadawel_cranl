import en from '@jadawel/modules/arabase/locales/en.json'
import ar from '@jadawel/modules/arabase/locales/ar.json'
import {
  ELEMENT_CATEGORIES,
  ELEMENT_GALLERY,
  galleryEntry,
  gallerySections,
} from '@jadawel/modules/arabase/builder/elementGallery'

const fakeType = (type, name, category = 'baseElement') => ({
  getType: () => type,
  name,
  description: `${name} element`,
  category: () => category,
  image: `${type}.png`,
})

describe('element gallery', () => {
  test('every registered element has a section, a preview and a line in both languages', () => {
    const { $registry } = useNuxtApp()
    const types = Object.values($registry.getAll('element'))

    expect(types.length).toBeGreaterThan(15)
    const keys = types.map((type) => type.getType())
    const missing = (lines) => keys.filter((key) => !lines[key])

    expect(missing(ELEMENT_GALLERY)).toEqual([])
    expect(missing(en.elementGallery.elements)).toEqual([])
    expect(missing(ar.elementGallery.elements)).toEqual([])
    for (const key of keys) {
      expect(ELEMENT_CATEGORIES).toContain(ELEMENT_GALLERY[key].category)
    }
    for (const category of ELEMENT_CATEGORIES) {
      expect(en.elementGallery.category[category]).toBeTruthy()
      expect(ar.elementGallery.category[category]).toBeTruthy()
    }
  })

  test('sections follow the gallery order and drop empty ones', () => {
    const types = [
      fakeType('table', 'Table'),
      fakeType('heading', 'Heading'),
      fakeType('text', 'Text'),
      fakeType('future', 'Future', 'formElement'),
    ]

    const sections = gallerySections(types)

    expect(sections.map((s) => s.category)).toEqual([
      'content',
      'data',
      'forms',
    ])
    expect(sections[0].elementTypes.map((t) => t.getType())).toEqual([
      'heading',
      'text',
    ])
    // An element the fork does not know keeps core's category and image.
    expect(galleryEntry(types[3])).toEqual({
      category: 'forms',
      tile: 'future.png',
    })
  })

  test('search matches names, descriptions and the gallery line', () => {
    const types = [fakeType('table', 'Table'), fakeType('heading', 'Heading')]
    const describe = (type) =>
      type.getType() === 'table' ? 'rows of data' : ''

    expect(
      gallerySections(types, { search: 'ROWS', describe }).flatMap((s) =>
        s.elementTypes.map((t) => t.getType())
      )
    ).toEqual(['table'])
    expect(gallerySections(types, { search: 'nothing' })).toEqual([])
  })
})
