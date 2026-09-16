import { readFileSync } from 'node:fs'

const gridStyles = readFileSync(
  'modules/core/assets/scss/components/views/grid.scss',
  'utf8'
)
const sidebarStyles = readFileSync(
  'modules/core/assets/scss/components/sidebar.scss',
  'utf8'
)
const headerStyles = readFileSync(
  'modules/core/assets/scss/components/header.scss',
  'utf8'
)
const dashboardStyles = readFileSync(
  'modules/core/assets/scss/components/dashboard.scss',
  'utf8'
)
const appUtilitiesStyles = readFileSync(
  'modules/core/assets/scss/components/app_utilities.scss',
  'utf8'
)
const buttonStyles = readFileSync(
  'modules/core/assets/scss/abstracts/_button.scss',
  'utf8'
)
const shareViewComponent = readFileSync(
  'modules/database/components/view/ShareViewLink.vue',
  'utf8'
)

describe('interface theme styling', () => {
  test('each table column header uses the selected interface color', () => {
    const columnRules = gridStyles.match(
      /\.grid-view__head & \{(?<rules>[^}]*)\}/s
    )?.groups.rules

    expect(columnRules).toBeDefined()
    expect(columnRules).toMatch(
      /background-color:\s*var\(--jadawel-header-background,\s*#f5f6f7\)/
    )
    expect(columnRules).toMatch(
      /border-inline-end-color:\s*var\(--jadawel-border-color,\s*#e7e9ec\)/
    )
    expect(columnRules).not.toMatch(
      /(?:background-color|border-inline-end-color):\s*\$palette-neutral-/
    )
  })

  test('table top bars and the workspace panel cap use the selected accent', () => {
    const workspaceSelectorRules = sidebarStyles.match(
      /\.sidebar__workspaces-selector \{(?<rules>[^}]*)\}/s
    )?.groups.rules
    const headerRules = headerStyles.match(/\.header \{(?<rules>[^}]*)\}/s)
      ?.groups.rules
    const dashboardHeaderRules = dashboardStyles.match(
      /\.dashboard__header \{(?<rules>[^}]*)\}/s
    )?.groups.rules

    expect(workspaceSelectorRules).toBeDefined()
    expect(headerRules).toBeDefined()
    expect(dashboardHeaderRules).toBeDefined()
    expect(workspaceSelectorRules).toMatch(
      /background-color:\s*\$color-primary-500/
    )
    expect(headerRules).toMatch(/background-color:\s*\$color-primary-500/)
    expect(dashboardHeaderRules).toMatch(/background:\s*\$white/)
    expect(dashboardHeaderRules).not.toMatch(
      /background:\s*\$color-primary-500/
    )
    expect(dashboardStyles).toMatch(
      /\.layout__col-2:has\(\.dashboard__header\) \{[^}]*background-color:\s*\$white/s
    )
    expect(dashboardStyles).toMatch(
      /\.dashboard__scroll-container \{[^}]*background:\s*\$white/s
    )
    expect(appUtilitiesStyles).toMatch(
      /\.layout__col-2:has\(\.dashboard__header\) \.app-utilities__item \{[^}]*color:\s*\$palette-neutral-800/s
    )
  })

  test('shared views and the grid menu match the other top bar controls', () => {
    const gridMenuRules = headerStyles.match(
      /\.header__filter-icon\.jadawel-icon-more-vertical \{(?<rules>[^}]*)\}/s
    )?.groups.rules

    expect(shareViewComponent).toMatch(/class="header__filter-link"/)
    expect(shareViewComponent).not.toMatch(/active--primary/)
    expect(gridMenuRules).toBeDefined()
    expect(gridMenuRules).toMatch(/color:\s*\$white/)
  })

  test('workspace avatars in the popup follow the selected color', () => {
    const popupAvatarRules = sidebarStyles.match(
      /\.dashboard__user-workspace-avatar \{(?<rules>[^}]*)\}/s
    )?.groups.rules

    expect(popupAvatarRules).toBeDefined()
    expect(popupAvatarRules).toMatch(/background:\s*\$color-primary-500/)
    expect(popupAvatarRules).not.toMatch(/\$palette-brand-/)
  })

  test('primary buttons use the selected interface color', () => {
    expect(buttonStyles).toMatch(/\$button-primary:\s*\$color-primary-500;/)
    expect(buttonStyles).toMatch(/\$background-hover:\s*\$color-primary-600,/)
    expect(buttonStyles).toMatch(/\$background-active:\s*\$color-primary-700,/)
    expect(buttonStyles).not.toMatch(
      /\$(?:button-primary|background-hover|background-active):\s*\$palette-brand-/
    )
  })
})
