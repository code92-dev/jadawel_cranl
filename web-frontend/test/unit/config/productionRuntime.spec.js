import productionConfig from '../../../config/nuxt.config.prod'

describe('production runtime configuration', () => {
  const originalClusterWorkers = process.env.NITRO_CLUSTER_WORKERS

  afterEach(() => {
    if (originalClusterWorkers === undefined) {
      delete process.env.NITRO_CLUSTER_WORKERS
    } else {
      process.env.NITRO_CLUSTER_WORKERS = originalClusterWorkers
    }
    vi.resetModules()
  })

  test('caches bundled translations across page reloads', () => {
    expect(productionConfig.i18n.experimental.cacheLifetime).toBe(86400)
    expect(productionConfig.i18n.experimental.httpCacheDuration).toBe(86400)
  })

  test('builds a clustered Nitro server', () => {
    expect(productionConfig.nitro.preset).toBe('node-cluster')
  })

  test('bounds the default production worker count', async () => {
    delete process.env.NITRO_CLUSTER_WORKERS
    vi.resetModules()

    await import('../../../env-remap.mjs')

    expect(process.env.NITRO_CLUSTER_WORKERS).toBe('1')
  })

  test('preserves an explicit production worker count', async () => {
    process.env.NITRO_CLUSTER_WORKERS = '4'
    vi.resetModules()

    await import('../../../env-remap.mjs')

    expect(process.env.NITRO_CLUSTER_WORKERS).toBe('4')
  })
})
