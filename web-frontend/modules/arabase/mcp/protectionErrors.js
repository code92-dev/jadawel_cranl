import { ResponseErrorMessage } from '@jadawel/modules/core/plugins/clientHandler'

/**
 * Messages for the protection API's own error codes, passed to `handleError`
 * as its specific error map. Without them a refusal to protect a field while
 * the server's protection vault is not configured would surface as the generic
 * "action not completed" toast.
 *
 * `MCP_PROTECTION_NOT_READY` is only answered by reactivation, with a 409,
 * when the issue that suspended protection still stands (the owner lost
 * access, the workspace is trashed or a protected field fails validation).
 */
export function protectionErrorMap(t) {
  return {
    ERROR_MCP_PROTECTION_NOT_READY: new ResponseErrorMessage(
      t('mcpProtection.notReadyTitle'),
      t('mcpProtection.notReadyDescription')
    ),
    MCP_PROTECTION_NOT_READY: new ResponseErrorMessage(
      t('mcpProtection.reactivateNotReadyTitle'),
      t('mcpProtection.reactivateNotReadyDescription')
    ),
  }
}
