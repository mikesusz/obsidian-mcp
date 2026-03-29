# Migration Guide: obsidian-mcp → markdown-vault-mcp (v3.0.0)

## Breaking Changes

### 1. Repository / Package Renamed

- Old: `obsidian-mcp`
- New: `markdown-vault-mcp`

**Action:** If you cloned the repo, your existing clone will continue to work via GitHub's redirect. No action required unless you have the old URL pinned somewhere.

### 2. MCP Server Name Changed

- Old: `"obsidian"` in your MCP client config
- New: `"markdown-vault"`

**Action:** Update your Claude Desktop (or other MCP client) config:

```json
{
  "mcpServers": {
    "markdown-vault": {
      "command": "/path/to/obsidian-mcp/.venv/bin/python",
      "args": ["-m", "markdown_vault_mcp.server"],
      "env": {
        "VAULT_PATH": "/path/to/your/markdown/files"
      }
    }
  }
}
```

### 3. Python Module Renamed

- Old: `python -m obsidian_mcp.server`
- New: `python -m markdown_vault_mcp.server`

**Action:** Update the `args` in your MCP client config (shown above).

### 4. Hardcoded Writable Notes Removed

**Old behavior:** The server maintained a whitelist of appendable files (defaulting to `__INBOX.md` and `__scratch.md`, customizable via `.obsidian-mcp.config.json`). Only files in that list could be appended to, and they had to be in the vault root.

**New behavior:** Any note with `agent_access: append` or `agent_access: edit` in its frontmatter is appendable. Notes without any frontmatter also default to `append` access. Subdirectory paths are now supported.

**Action:** Add frontmatter to any files you want agents to append to:

```yaml
---
agent_access: append
---

# My Inbox

Content here…
```

**No action needed if:**
- Your notes already have `agent_access` frontmatter (they'll keep working as-is)
- You're fine with the default `append` access for notes without frontmatter

### 5. `.obsidian-mcp.config.json` No Longer Used

The vault-level config file for the writable notes whitelist is no longer read. All permissions are controlled via frontmatter.

**Action:** You can delete `.obsidian-mcp.config.json` from your vault — it's now ignored.

---

## Non-Breaking Changes

- All `agent_access` permission values (`edit`, `append`, `read`, `hidden`) work the same
- Backward compatibility for old `full` / `none` values still applies (`full` → `edit`, `none` → `read`)
- All tool names and parameter names are unchanged
- `VAULT_PATH` environment variable is unchanged

---

## `list_writable_notes` Response Format Change

The response shape changed slightly:

**Old:**
```json
{
  "writable_notes": [
    { "path": "__INBOX.md", "exists": true, "purpose": "Quick capture inbox" }
  ]
}
```

**New:**
```json
{
  "writable_notes": [
    { "path": "__INBOX.md", "access_level": "append" }
  ]
}
```

The `purpose` field (from the old config file) and the `exists` field (always `true` now since we scan existing files) are gone. `access_level` shows whether the note has `"append"` or `"edit"` access.
