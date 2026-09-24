from enum import StrEnum


class MCPErrorCode(StrEnum):
    ACCESS_DENIED = "MCP_ACCESS_DENIED"
    TOOL_NOT_FOUND = "MCP_TOOL_NOT_FOUND"
    TOOL_FAILED = "MCP_TOOL_FAILED"
    PROTECTION_UNAVAILABLE = "PROTECTION_UNAVAILABLE"


# One constant per code, so a model can explain the failure without the error
# ever carrying caller input, cell values, or exception text. A message must not
# say which check failed: distinguishing a rejected token from an unavailable
# vault would turn the error into an oracle.
SAFE_MCP_ERROR_MESSAGES: dict[MCPErrorCode, str] = {
    MCPErrorCode.ACCESS_DENIED: (
        "Access denied: this MCP URL is invalid or revoked, or its owner can no "
        "longer access the workspace. Ask the workspace owner for a new MCP URL."
    ),
    MCPErrorCode.TOOL_NOT_FOUND: (
        "No enabled tool has this name. Call tools/list for the available tools."
    ),
    MCPErrorCode.TOOL_FAILED: (
        "The tool call failed. Check the ids and field names against "
        "get_table_schema and the arguments against the tool's input schema, "
        "then retry with corrected arguments."
    ),
    MCPErrorCode.PROTECTION_UNAVAILABLE: (
        "Blocked to keep protected fields safe. This endpoint protects fields "
        "in the requested table, and the call either needs the server's "
        "field-protection service, which is not available, or uses an operation "
        "that is not allowed on protected data (search, more than 200 rows, or "
        "a protection token outside the exact cell it came from). Retrying the "
        "same call will not help. If plain reads of this table also fail, tell "
        "the user a workspace administrator must check the MCP protection "
        "readiness status."
    ),
}


class SafeMCPToolError(Exception):
    """A content-blind MCP failure that is safe to map to the protocol."""

    def __init__(self, code: MCPErrorCode, *, retryable: bool):
        super().__init__(code.value)
        self.code = code
        self.retryable = retryable
