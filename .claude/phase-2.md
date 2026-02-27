## Obsidian MCP Server - Phase 2: Write Operations

**Goal**: Add safe write operations to specific whitelisted files for quick capture and list management.

**What's changing:**
- Add write capability to a small, controlled set of files
- Maintain all Phase 1 read-only functionality
- Safety-first approach with hardcoded whitelist

**New MCP Tools:**

### 1. append_to_note
**Description**: Append content to the end of a whitelisted note

**Input:**
- `note_path` (string, required) - Must be in whitelist
- `content` (string, required) - Text to append
- `add_timestamp` (boolean, optional, default: true) - Prepend timestamp to content

**Returns:**
```json
{
  "success": true,
  "note_path": "string",
  "appended_content": "string",
  "message": "Successfully appended to [note]"
}
```

**Error handling:**
- Return error if note_path not in whitelist
- Return error if file doesn't exist
- Create file if it doesn't exist (with user confirmation in error message)

**Implementation notes:**
- Always append, never overwrite
- Add newline before appended content if file doesn't end with one
- If `add_timestamp` is true, format: `\n## YYYY-MM-DD HH:MM\n{content}\n`

### 2. list_writable_notes
**Description**: Show which notes support write operations

**Input:** None

**Returns:**
```json
{
  "writable_notes": [
    {
      "path": "__INBOX.md",
      "exists": true,
      "purpose": "Quick capture inbox"
    },
    {
      "path": "__scratch.md",
      "exists": true,
      "purpose": "Temporary notes and thoughts"
    },
    {
      "path": "bands.md",
      "exists": false,
      "purpose": "Music to check out"
    },
    {
      "path": "books.md",
      "exists": true,
      "purpose": "Reading list"
    }
  ]
}
```

**Hardcoded Whitelist** (in `vault.py` or `server.py`):
```python
WRITABLE_NOTES = {
    "__INBOX.md": "Quick capture inbox",
    "__scratch.md": "Temporary notes and thoughts",
    "bands.md": "Music to check out",
    "books.md": "Reading list"
}
```

**Safety Requirements:**
- Whitelist must be hardcoded in source, not configurable via env vars
- No path traversal allowed (validate note_path is in whitelist exactly)
- Files must be in vault root (no subfolder paths in whitelist for Phase 2)
- Log all write operations to stdout/stderr with timestamp

**Testing checklist:**
1. Append to existing file works
2. Timestamp formatting is correct
3. Attempting to write to non-whitelisted file fails gracefully
4. Path traversal attempts (e.g., `../etc/passwd`) are blocked
5. Creating new file works if in whitelist but doesn't exist
6. Multiple appends to same file work correctly

**Example Usage:**
```
User: "Add The Expanse to my books list"
→ append_to_note("books.md", "- The Expanse", false)

User: "Remember to order furnace filters"
→ append_to_note("__INBOX.md", "Order furnace filters", true)
→ Result:
## 2026-02-24 14:30
Order furnace filters
```

**README Updates:**
- Document the whitelist and how to modify it
- Add examples of write operations
- Clarify Phase 2 is append-only, not full editing

**Future Phase 3 considerations** (not in scope now):
- Full note editing
- Template-based note creation
- Frontmatter manipulation
- Folder support for writable files

---
