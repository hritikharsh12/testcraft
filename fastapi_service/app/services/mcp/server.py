"""
Runs this project's test-generation pipeline as an MCP server, so any
MCP-compatible client (Claude Desktop, an agent framework, another service)
can call it directly instead of going through the REST API.

Run with:
    python -m app.services.mcp.server

Then point an MCP client at it over stdio. Example Claude Desktop config
entry (claude_desktop_config.json):

    "test-case-generator": {
      "command": "python",
      "args": ["-m", "app.services.mcp.server"],
      "cwd": "/absolute/path/to/fastapi_service"
    }

Each tool that touches user data takes `access_token` as a plain string
argument — MCP tool calls have no HTTP Authorization header to piggyback
on, so the token issued by the Django /auth/login/ endpoint is passed
explicitly and verified the same way the REST API verifies it.
"""

from mcp.server.fastmcp import FastMCP

from app.core.logging import setup_logging
from app.services.mcp import tools
from app.services.mcp.tools import MCPToolError

setup_logging()

mcp = FastMCP("test-case-generator")


@mcp.tool()
async def analyze_code(source_code: str, filename: str) -> dict:
    """
    Parse a source file and return its structure: functions, classes,
    imports, and static-analysis warnings (e.g. missing docstrings).
    No authentication required — pure analysis, nothing persisted.
    """
    return await tools.analyze_code(source_code=source_code, filename=filename)


@mcp.tool()
async def generate_tests(access_token: str, source_code: str, filename: str) -> dict:
    """
    Generate a runnable test file plus improvement suggestions for the
    given source code, using retrieval-augmented prompting against this
    project's testing-conventions knowledge base. Requires a valid access
    token from the Django auth service. Rate-limited per user.
    """
    try:
        return await tools.generate_tests(access_token=access_token, source_code=source_code, filename=filename)
    except MCPToolError as exc:
        return {"error": str(exc)}


@mcp.tool()
async def suggest_improvements(access_token: str, source_code: str, filename: str) -> dict:
    """
    Lightweight code-review pass: returns specific improvement suggestions
    only, without generating a full test file or persisting anything.
    Requires a valid access token. Rate-limited per user.
    """
    try:
        return await tools.suggest_improvements(access_token=access_token, source_code=source_code, filename=filename)
    except MCPToolError as exc:
        return {"error": str(exc)}


if __name__ == "__main__":
    mcp.run()  # defaults to stdio transport
