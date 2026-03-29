# Phase 4.0 (v3.0.0) - Generic Rebrand to markdown-vault-mcp

## Overview

Rebrand `obsidian-mcp` to `markdown-vault-mcp` - a generic markdown file manager with frontmatter-based permissions. Remove Mike-specific hardcoded assumptions and make it work with **any** folder of markdown files.

## Philosophy

**“This has nothing to do with Obsidian. It points at a folder full of markdown files.”**

Works with:

- ✅ Obsidian vaults
- ✅ Static site generators (Hugo, Jekyll, Astro)
- ✅ Note-taking apps (Bear, Typora, iA Writer)
- ✅ Any folder of `.md` files

## Breaking Changes (v2.0.0 → v3.0.0)

### 1. Repository Rename

- **Old:** `obsidian-mcp`
- **New:** `markdown-vault-mcp`

### 2. Package/Command Rename

- **Old:** `obsidian` (MCP server name in claude_desktop_config.json)
- **New:** `markdown-vault` (or `mdvault`)

### 3. Environment Variable Rename

- **Old:** `VAULT_PATH`
- **New:** `MARKDOWN_PATH` (or keep VAULT_PATH for backward compat?)

### 4. Remove Hardcoded WRITABLE_NOTES List

**Current implementation (v2.0.0):**

```python
# vault.py
WRITABLE_NOTES = [
    '__INBOX.md',
    '__scratch.md',
    '_books.md',
    # ... other Mike-specific files
]

def append_to_note(self, note_path: str, content: str) -> dict:
    if note_path not in WRITABLE_NOTES:
        raise ValueError(f"Note '{note_path}' is not in the writable notes list")
    # ... rest of logic
```

**New implementation (v3.0.0):**

```python
# vault.py
# NO hardcoded list!

def append_to_note(self, note_path: str, content: str, add_timestamp: bool = True) -> dict:
    """Append content to a note. Requires agent_access: 'append' or 'edit'."""
    
    # Check permission via frontmatter
    allowed, error_msg = self._check_agent_access(note_path, required_level='append')
    if not allowed:
        raise PermissionError(error_msg)
    
    # ... rest of append logic
```

**Migration:**

- Users add `agent_access: append` to any file they want appendable
- No code changes needed - just frontmatter

-----

## Implementation Tasks

### Task 1: Repository & Package Rename

**Files to update:**

- `pyproject.toml` - package name, description
- `README.md` - title, all references
- `setup.py` (if exists) - package name
- `.github/` workflows - update references
- All tool descriptions in `server.py`

**New package name:** `markdown-vault-mcp`

**New description:**

> Agent-controlled markdown files with frontmatter-based permissions. Works with Obsidian, static site generators, or any folder of `.md` files.

### Task 2: Remove WRITABLE_NOTES Constant

**File:** `vault.py`

**Changes:**

1. Delete `WRITABLE_NOTES` constant entirely
2. Update `append_to_note()` to check `agent_access` frontmatter instead
3. Update `list_writable_notes()` to return all notes with `agent_access: append` or `agent_access: edit`

**Before:**

```python
WRITABLE_NOTES = ['__INBOX.md', '__scratch.md', '_books.md']

def list_writable_notes(self) -> list:
    return WRITABLE_NOTES
```

**After:**

```python
def list_writable_notes(self) -> list:
    """List all notes that agents can append to (append or edit access)."""
    all_notes = self._get_all_notes()
    writable = []
    
    for note in all_notes:
        if not self._is_agent_visible(note['path']):
            continue
        
        note_meta = self._get_note_metadata(note['path'])
        if not note_meta or 'frontmatter' not in note_meta:
            # No frontmatter = default 'append' access
            writable.append(note)
            continue
            
        agent_access = self._normalize_access(
            note_meta['frontmatter'].get('agent_access', 'append')
        )
        
        if agent_access in ['append', 'edit']:
            writable.append(note)
    
    return writable
```

### Task 3: Update Tool Descriptions

**File:** `server.py`

**Update all tool descriptions to:**

- Remove Obsidian-specific language
- Use generic “markdown vault” or “note repository” terminology
- Emphasize frontmatter-based permissions

**Example:**

```python
# BEFORE
"description": "Search notes in your Obsidian vault by content or title..."

# AFTER  
"description": "Search markdown notes by content or title (case-insensitive)..."
```

### Task 4: Update README.md

**Major sections to rewrite:**

#### New Title & Tagline

```markdown
# markdown-vault-mcp

Agent-controlled markdown files with frontmatter-based permissions.

Works with Obsidian, static site generators (Hugo, Jekyll, Astro), note-taking apps (Bear, Typora), or any folder of `.md` files.
```

#### Installation Section

```markdown
## Installation

Point the MCP server at any folder containing markdown files:

```json
{
  "mcpServers": {
    "markdown-vault": {
      "command": "python",
      "args": ["-m", "markdown_vault_mcp"],
      "env": {
        "MARKDOWN_PATH": "/path/to/your/markdown/files"
      }
    }
  }
}
```

**For Obsidian users:** Set `MARKDOWN_PATH` to your vault folder (e.g., `/Users/you/Documents/MyVault`)

```
#### Permission System Section
**Emphasize frontmatter control:**
```markdown
## Permission System

Control agent access by adding frontmatter to any markdown file:

```yaml
---
agent_access: edit    # Full editing
agent_access: append  # Add content only
agent_access: read    # View but don't modify
agent_access: hidden  # Completely invisible to agents
---
```

Files without frontmatter default to `append` access (safe, conservative).

**No configuration files. No hardcoded lists. Just frontmatter.**

```
#### Add "Works With" Section
```markdown
## Works With

- **Obsidian** - Point at your vault folder
- **Hugo/Jekyll** - Point at `content/` folder
- **Bear/Typora** - Point at your notes folder
- **Plain markdown** - Point at any folder of `.md` files

The server doesn't care about your note-taking app — it just needs markdown files with optional YAML frontmatter.
```

### Task 5: Update Templates

**File:** `templates/examples/MEETING_NOTES.md`

Update header comment:

```markdown
<!-- 
This template works with markdown-vault-mcp.
Add it to any markdown folder: Obsidian vaults, Hugo sites, or plain folders.
-->
```

### Task 6: Migration Guide

**Create:** `MIGRATION.md`

```markdown
# Migration Guide: v2.0.0 → v3.0.0

## Breaking Changes

### 1. Repository Renamed
- Old: `obsidian-mcp`  
- New: `markdown-vault-mcp`

**Action:** Update your git remote if you're tracking the repo.

### 2. MCP Server Name Changed  
- Old: `"obsidian"` in claude_desktop_config.json
- New: `"markdown-vault"`

**Action:** Update your Claude Desktop config:
```json
{
  "mcpServers": {
    "markdown-vault": {  // ← Changed from "obsidian"
      "command": "python",
      "args": ["-m", "markdown_vault_mcp"],
      "env": {
        "MARKDOWN_PATH": "/path/to/vault"  // ← Can keep or rename from VAULT_PATH
      }
    }
  }
}
```

### 3. Hardcoded Writable Notes Removed

**Old behavior:** Server had hardcoded list of appendable files (`__INBOX.md`, `__scratch.md`, etc.)

**New behavior:** ANY file with `agent_access: append` or `agent_access: edit` in frontmatter is appendable.

**Action:** Add frontmatter to files you want agents to append to:

```yaml
---
agent_access: append
---

# My Inbox
Content here...
```

**No action needed if:**

- Files already have `agent_access` frontmatter (they’ll keep working)
- You’re fine with the default `append` access for files without frontmatter

## Non-Breaking Changes

- All permission values (`edit`, `append`, `read`, `hidden`) work the same
- Backward compatibility for old `full`/`none` values still works
- All tools have the same parameter names

```
---

## Testing Checklist

After implementation, verify:

- [ ] Package installs as `markdown-vault-mcp`
- [ ] MCP server registers in Claude Desktop as `"markdown-vault"`
- [ ] `list_writable_notes` returns notes with `agent_access: append` or `edit`
- [ ] `append_to_note` works on any file with appropriate frontmatter
- [ ] `append_to_note` rejects files with `agent_access: read` or `hidden`
- [ ] No references to hardcoded `WRITABLE_NOTES` remain in code
- [ ] README accurately reflects new branding and use cases
- [ ] Templates updated with new header comments
- [ ] All tool descriptions are Obsidian-agnostic

---

## Communication Plan

### GitHub Release v3.0.0

**Title:** Generic Rebrand - Now Works with Any Markdown Folder

**Body:**
```markdown
## 🎉 v3.0.0 - The Generic Rebrand

`obsidian-mcp` is now `markdown-vault-mcp` - a tool for **any** markdown folder, not just Obsidian vaults.

### What Changed

✨ **Works with more tools:**
- Obsidian vaults ✅
- Hugo/Jekyll/Astro sites ✅  
- Bear, Typora, iA Writer ✅
- Plain markdown folders ✅

🔒 **Smarter permissions:**
- No more hardcoded file lists!
- Add `agent_access: append` to ANY file you want appendable
- Control everything via frontmatter, not config files

### Breaking Changes

1. **Repo renamed:** `obsidian-mcp` → `markdown-vault-mcp`
2. **Config update needed:** Change `"obsidian"` to `"markdown-vault"` in your Claude Desktop config
3. **Hardcoded writable notes removed:** Use frontmatter instead (see Migration Guide)

👉 **[Full Migration Guide](MIGRATION.md)**

### Why the rebrand?

The tool never really needed Obsidian. It works with any folder of markdown files. The new name reflects that reality and helps more people discover it.

**For Obsidian users:** Everything still works! Just update your config and you're good to go.

### Credits

Inspired by users asking: "Can I use this with my Hugo site?" and "How do I hide some files from the agent?"

The answer is now: Yes, and just add `agent_access: hidden` to the frontmatter. 🎊
```

-----

## Timeline

**Recommended approach:**

1. Create `markdown-vault-mcp` as NEW repo (keep `obsidian-mcp` archived for now)
2. Add deprecation notice to `obsidian-mcp` README pointing to new repo
3. Tag v3.0.0 in new repo
4. Update all documentation
5. Archive old repo after 30-60 days

OR

**Fast approach:**

1. Rename existing repo
2. Tag v3.0.0
3. GitHub auto-redirects old URLs
4. Users get migration guide

-----

## Open Questions for Mike

1. **Env var name:** Keep `VAULT_PATH` for backward compat, or rename to `MARKDOWN_PATH`?
2. **MCP server name:** `markdown-vault` or `mdvault` or `md-vault`?
3. **Repo strategy:** New repo or rename existing?
4. **Old repo:** Archive immediately or deprecation period?

-----

## Success Criteria

v3.0.0 is successful when:

- ✅ Someone can point it at a Hugo site and it just works
- ✅ No Obsidian-specific assumptions in code or docs
- ✅ Frontmatter controls all permissions (no hardcoded lists)
- ✅ README shows multiple use cases beyond Obsidian
- ✅ Obsidian users can still use it without friction