/**
 * Error codes of `/arabase/my-dashboards/` with a message under
 * `myDashboards.errors`. A throttled password guess (429) keeps core's own
 * message.
 */
export const KNOWN_ERRORS = [
  'ERROR_SAVED_DASHBOARD_LINK_INVALID',
  'ERROR_SAVED_DASHBOARD_PASSWORD_INCORRECT',
  'ERROR_SAVED_DASHBOARD_UNAVAILABLE',
  'ERROR_SAVED_DASHBOARD_UNREACHABLE',
]

export function errorCode(error) {
  return error?.handler?.code || null
}

/**
 * Shows a known error in a component using the `error` mixin, or leaves it to
 * the mixin's generic handling.
 */
export function showSavedDashboardError(vm, error) {
  const code = errorCode(error)
  if (KNOWN_ERRORS.includes(code)) {
    vm.showError(
      vm.$t(`myDashboards.errors.${code}.title`),
      vm.$t(`myDashboards.errors.${code}.message`)
    )
    error.handler.handled()
    return
  }
  vm.handleError(error, 'dashboard')
}
