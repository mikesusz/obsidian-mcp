## Phase 3.6: Full Edit Capabilities

**Goal:** Add tools to update, replace, and delete notes that have `agent_access: "full"` in frontmatter.

### New Tools

**`update_note`**

- **Description:** Replace the entire content of a note (preserves frontmatter)
- **Params:**
  - `note_path` (string, required) - Path to note relative to vault root
  - `new_content` (string, required) - New content for the note body
- **Permission check:** Requires `agent_access: "full"` in note's frontmatter
- **Behavior:**
  - Read existing note
  - Parse frontmatter
  - Check `agent_access` field
  - If "full": Replace body content, keep frontmatter intact
  - If not "full": Return error with clear message
- **Error message:** "Cannot update note: requires agent_access: 'full' in frontmatter. Current access: [value]"

**`replace_in_note`**

- **Description:** Find and replace specific text in a note
- **Params:**
  - `note_path` (string, required) - Path to note
  - `old_text` (string, required) - Text to find (must be exact match)
  - `new_text` (string, required) - Replacement text
- **Permission check:** Requires `agent_access: "full"`
- **Behavior:**
  - Read note, check permissions
  - Find `old_text` in body (case-sensitive)
  - Replace with `new_text`
  - If `old_text` not found, return error: "Text not found in note"
- **Safety:** Only replaces in body, never in frontmatter

**`update_section`** (optional but recommended)

- **Description:** Replace content under a specific heading
- **Params:**
  - `note_path` (string, required) - Path to note
  - `heading` (string, required) - Heading text (e.g., "SYNOPSIS:", "## Next Steps")
  - `new_content` (string, required) - New content for that section
- **Permission check:** Requires `agent_access: "full"`
- **Behavior:**
  - Find heading in note
  - Replace content between that heading and next heading (or end of file)
  - Preserve heading itself
- **Error if heading not found:** "Heading '[heading]' not found in note"

### Permission Check Implementation

Add helper function in `vault.py`:

```python
def check_note_permission(note_path: str, required_access: str) -> tuple[bool, str]:
    """
    Check if note has required agent_access permission.
    Returns (allowed: bool, current_access: str)
    """
    content = read_note(note_path)
    parsed = frontmatter.loads(content)

    current_access = parsed.metadata.get('agent_access', 'none')

    # Permission hierarchy: full > append > none
    if required_access == 'full':
        allowed = current_access == 'full'
    elif required_access == 'append':
        allowed = current_access in ['full', 'append']
    else:
        allowed = True  # 'none' = read-only, always allowed

    return allowed, current_access
```

### Error Handling

All write tools should return clear, actionable errors:

```python
if not allowed:
    return {
        "success": False,
        "error": f"Insufficient permissions. This note has agent_access: '{current}', but this operation requires: '{required}'. Add agent_access: '{required}' to the note's frontmatter to enable this operation."
    }
```

### Tool Registration

Update `server.py` to register new tools:

- `update_note`
- `replace_in_note`
- `update_section` (if implemented)

### Testing Strategy

After implementation, test with:

1. **Full access note:** Create note with `agent_access: full`, try all operations
2. **Append-only note:** Try edit operations, verify they're blocked
3. **No access note:** Try edit operations, verify error messages
4. **Edge cases:**
   - Empty content
   - Very long content
   - Multiline replacements
   - Headings that don't exist

### Documentation

Update README with:

- New tool descriptions
- Permission requirements table
- Examples of each tool
- Common error messages and solutions
