from __future__ import annotations

from pathlib import Path

from agent_core import ExecutionContext
from agent_core.spi import AuthorizationResult, ToolResult, build_tool_definition


class ReadWorkspaceFileTool:
    """Read one text file after the policy has resolved it inside workspace/."""

    name = "read_workspace_file"
    description = "Read a UTF-8 text file from the configured workspace."

    def schema(self):
        return build_tool_definition(
            name=self.name,
            description=self.description,
            parameters={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path relative to workspace/, for example theme.txt.",
                    }
                },
                "required": ["path"],
                "additionalProperties": False,
            },
        )

    def execute(self, arguments: dict, context: ExecutionContext) -> ToolResult:
        path = Path(str(arguments["path"])).resolve()

        # Defense in depth: the policy resolves the path first, but the tool
        # still refuses anything outside the current execution scope.
        if not context.is_path_allowed(path):
            return ToolResult(False, f"Path outside workspace: {path}")
        if not path.is_file():
            return ToolResult(False, f"File not found: {path}")

        return ToolResult(True, path.read_text(encoding="utf-8"))


def validate_workspace_read(arguments: dict, context: ExecutionContext) -> AuthorizationResult:
    """Policy: accept only paths that resolve inside allowed_read_roots."""

    raw_path = arguments.get("path")
    if not isinstance(raw_path, str) or not raw_path.strip():
        return AuthorizationResult(False, "Missing path")

    requested = Path(raw_path.strip())
    candidates = (
        [requested.resolve()]
        if requested.is_absolute()
        else [(root / requested).resolve() for root in context.allowed_read_roots()]
    )

    for candidate in candidates:
        if context.is_path_allowed(candidate):
            arguments["path"] = str(candidate)
            return AuthorizationResult(True, "allowed")

    return AuthorizationResult(False, f"Path outside workspace: {requested}")
