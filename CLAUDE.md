# Claude Code Instructions

## Frontend Verification

**REQUIRED:** Any implementation that can be verified via the frontend MUST be verified using the Playwright MCP before declaring the task complete.

- Use `mcp__playwright__browser_navigate` to open the relevant page
- Use `mcp__playwright__browser_snapshot` and `mcp__playwright__browser_take_screenshot` to confirm the UI renders correctly
- Verify the specific feature/fix is visible and functional in the browser
- Do not rely solely on code review or unit tests for frontend changes — always do a live browser check via Playwright MCP
