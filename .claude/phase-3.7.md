WRITING PROJECT:
Obsidian MCP Phase 3.7 - Refactor agent_access for Human-Friendly Visibility Controls

SYNOPSIS:
Refactor the `agent_access` frontmatter field to use clearer, human-brain-friendly values and add true visibility controls. Current values (`full`, `append`, `none`) are confusing - `none` sounds like "no access" but actually means "read-only". New values will be intuitive and include a `hidden` option to completely exclude files from agent visibility.

AUDIENCE:
Claude Code for implementation, future obsidian-mcp users who need clear permission semantics

GOALS:

- Replace confusing `full`/`none` with clear `edit`/`read` values
- Add `hidden` value for complete invisibility to agents
- Maintain backward compatibility during migration
- Update all tool descriptions and templates
- Add visibility filtering to list_notes, search_notes, get_note

SECTION OUTLINE:

## Current State (Phase 3.6)

**Values:**

- `full` - Agent can edit freely (update_note, replace_in_note, update_section)
- `append` - Agent can only add content (append_to_note)
- `none` - Agent can READ but NOT edit (confusing name!)

**Problem:**
Users expect `none` to mean "no access" but it actually means "read-only"

## New Values (Phase 3.7)

**Proposed:**

- `edit` - Full editing capability (replaces `full`)
- `append` - Can only add content (unchanged)
- `read` - Can view but not modify (replaces `none`)
- `hidden` - Cannot see, search, or access at all (NEW)

**Permission Hierarchy:**

```
hidden < read < append < edit
  ↓       ↓       ↓       ↓
invisible view-only add-only edit-freely
```

## Implementation Tasks

### 1. Update Permission Check Function

File: `vault.py`

```python
def _check_agent_access(self, note_path: str, required_level: str) -> tuple[bool, str]:
    """Check if agent has required access level for a note."""
    note = self._get_note_metadata(note_path)

    if not note or 'frontmatter' not in note:
        return False, f"Could not read frontmatter from '{note_path}'"

    agent_access = note['frontmatter'].get('agent_access', 'append')

    # Map old values to new values for backward compatibility
    legacy_map = {
        'full': 'edit',
        'none': 'read'
    }
    agent_access = legacy_map.get(agent_access, agent_access)

    # Permission hierarchy: hidden < read < append < edit
    levels = {'hidden': 0, 'read': 1, 'append': 2, 'edit': 3}

    if agent_access not in levels:
        return False, f"Invalid agent_access value: '{agent_access}'"

    required_level_num = levels.get(required_level, 0)
    current_level_num = levels.get(agent_access, 0)

    if current_level_num < required_level_num:
        return False, f"Note '{note_path}' requires agent_access: '{required_level}' or higher (currently: '{agent_access}')"

    return True, ""
```

### 2. Add Visibility Filtering

File: `vault.py`

```python
def _is_agent_visible(self, note_path: str) -> bool:
    """Check if note should be visible to agent at all."""
    note = self._get_note_metadata(note_path)
    if not note or 'frontmatter' not in note:
        return True  # No frontmatter = visible by default

    agent_access = note['frontmatter'].get('agent_access', 'append')

    # Map old values
    if agent_access == 'full':
        agent_access = 'edit'
    elif agent_access == 'none':
        agent_access = 'read'

    return agent_access != 'hidden'

def list_notes(self, folder: Optional[str] = None) -> list:
    """List all notes, excluding hidden ones."""
    notes = self._get_all_notes(folder)
    return [n for n in notes if self._is_agent_visible(n['path'])]

def search_notes(self, query: str) -> list:
    """Search notes, excluding hidden ones from results."""
    # ... existing search logic ...
    results = # ... search results
    return [r for r in results if self._is_agent_visible(r['path'])]

def get_note(self, note_path: str) -> dict:
    """Get note content, blocking access to hidden notes."""
    if not self._is_agent_visible(note_path):
        raise ValueError(f"Note '{note_path}' is not accessible to agents")
    # ... rest of existing logic ...
```

### 3. Update Tool Descriptions

File: `server.py`

Update tool descriptions to reflect new values:

- `create_note_from_template`: Change enum from `["full", "append", "none"]` to `["edit", "append", "read", "hidden"]`
- Update description text to use new terminology
- Update natural language inference examples

### 4. Update Templates

File: `templates/WRITING PROJECT.md` (and others)

Change:

```yaml
---
agent_access: { { AGENT_ACCESS } }
---
```

Update any template documentation to reference new values.

### 5. Migration Notes

**Backward Compatibility:**

- Old `full` → automatically mapped to `edit`
- Old `none` → automatically mapped to `read`
- Old `append` → stays `append`
- No user action required for existing notes

**Breaking Changes:**

- None - all old values are mapped transparently

NOTES+REFERENCES:

## Natural Language Inference Guide

When users create notes, infer `agent_access` from phrasing:

| User says                                                  | Set to             |
| ---------------------------------------------------------- | ------------------ |
| "you can edit this" / "fully editable" / "you can modify"  | `edit`             |
| "you can add to this" / "append-only"                      | `append`           |
| "read-only" / "just for reference" / "I'll edit this"      | `read`             |
| "this is private" / "keep this hidden" / "don't show this" | `hidden`           |
| No instruction                                             | `append` (default) |

## Testing Checklist

- [ ] Notes with `agent_access: edit` can be edited
- [ ] Notes with `agent_access: append` can only be appended to
- [ ] Notes with `agent_access: read` can be viewed but not modified
- [ ] Notes with `agent_access: hidden` don't appear in list_notes
- [ ] Notes with `agent_access: hidden` don't appear in search_notes
- [ ] Notes with `agent_access: hidden` raise error on get_note
- [ ] Old `full` values work as `edit`
- [ ] Old `none` values work as `read`
- [ ] Tool descriptions show correct enum values

## Files to Update

- `vault.py` - permission checking, visibility filtering
- `server.py` - tool descriptions, enum values
- `templates/*.md` - documentation (if any references exist)

WORK:
[Ready for Claude Code implementation]
