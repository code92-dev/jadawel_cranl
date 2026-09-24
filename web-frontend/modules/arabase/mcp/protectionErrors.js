import { ResponseErrorMessage } from '@jadawel/modules/core/plugins/clientHandler'

/**
 * Messages for the protection API's own error codes, passed to `handleError`
 * as its specific error map. Without them a refusal to protect a field while
 * the server's protection vault is not configured would surface as the generic
 * "action not completed" toast.
 */
export function protectionErrorMap(t) {
  return {
    ERROR_MCP_PROTECTION_NOT_READY: new ResponseErrorMessage(
      t('mcpProtection.notReadyTitle'),
      t('mcpProtection.notReadyDescription')
    ),
  }
}
