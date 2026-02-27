# obsidian-mcp

A stdio MCP server for querying and capturing to an Obsidian vault. Provides full read access and append-only write access to a small, hardcoded whitelist of notes.

## Requirements

- Python 3.10+
- An Obsidian vault on your local filesystem

## Installation

```bash
# Clone / navigate to the project
cd obsidian-mcp

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# Install the package and its dependencies
pip install -e .
```

## Configuration

Copy the example env file and set your vault path:

```bash
cp .env.example .env
```

Edit `.env`:

```env
VAULT_PATH=/path/to/your/obsidian/vault
```

## Running the server

```bash
python -m obsidian_mcp.server
```

Or via the installed script:

```bash
obsidian-mcp
```

The server communicates over stdio and is launched by your MCP host.

## MCP Client Configuration

Most MCP clients that support stdio servers accept a configuration block like this:

```json
{
  "mcpServers": {
    "obsidian": {
      "command": "/path/to/obsidian-mcp/.venv/bin/python",
      "args": ["-m", "obsidian_mcp.server"],
      "env": {
        "VAULT_PATH": "/path/to/your/vault"
      }
    }
  }
}
```

Use the full path to the Python binary inside your virtualenv so the correct dependencies are picked up. The `VAULT_PATH` env var can be set here instead of (or in addition to) the `.env` file — values passed by the client take precedence.

Consult your MCP client's documentation for where to place this config.

## Available Tools

### `search_notes`

Search notes by title or content (case-insensitive). Returns up to 10 results.

**Input:**
- `query` (string, required) — term to search for

**Example result:**
```json
[
  {
    "title": "Meeting Notes",
    "path": "work/Meeting Notes.md",
    "snippet": "…discussed the new obsidian plugin architecture…",
    "relevance_score": 7.0
  }
]
```

**Example queries to test:**
- `search_notes` with `query: "project"` — find all notes mentioning "project"
- `search_notes` with `query: "TODO"` — surface action items across the vault

---

### `get_note`

Retrieve the full content and metadata of a specific note.

**Input:**
- `note_path` (string, required) — path relative to vault root, e.g. `"folder/My Note.md"`

**Example result:**
```json
{
  "title": "My Note",
  "path": "folder/My Note.md",
  "content": "# My Note\n\nBody text here…",
  "frontmatter": { "tags": ["idea"], "created": "2024-01-01" },
  "modified": "2024-06-15T10:30:00",
  "size": 1024
}
```

**Example queries to test:**
- `get_note` with `note_path: "Daily/2024-01-15.md"` — read a daily note
- `get_note` with `note_path: "README.md"` — read the vault's root README

---

### `list_notes`

List all markdown notes in the vault (or a subfolder).

**Input:**
- `folder` (string, optional) — subfolder path relative to vault root

**Example result:**
```json
[
  { "title": "Home", "path": "Home.md", "size": 512, "modified": "2024-06-01T09:00:00" },
  { "title": "Daily Note", "path": "Daily/2024-01-15.md", "size": 256, "modified": "2024-01-15T08:00:00" }
]
```

**Example queries to test:**
- `list_notes` with no arguments — see every note in the vault
- `list_notes` with `folder: "Projects"` — list only notes in the Projects folder

---

### `list_writable_notes`

Show which notes support write (append) operations, and whether each one currently exists in the vault.

**Input:** none

**Example result:**
```json
{
  "writable_notes": [
    { "path": "__INBOX.md",  "exists": true,  "purpose": "Quick capture inbox" },
    { "path": "__scratch.md","exists": true,  "purpose": "Temporary notes and thoughts" },
    { "path": "bands.md",   "exists": false, "purpose": "Music to check out" },
    { "path": "books.md",   "exists": true,  "purpose": "Reading list" }
  ]
}
```

---

### `append_to_note`

Append content to the end of a whitelisted note. This is the only write operation — it never overwrites existing content. If the note doesn't exist yet, it is created.

**Input:**
- `note_path` (string, required) — filename of a writable note, e.g. `"books.md"`
- `content` (string, required) — text to append
- `add_timestamp` (boolean, optional, default: `true`) — if true, inserts a `## YYYY-MM-DD HH:MM` heading before the content

**Example result:**
```json
{
  "success": true,
  "note_path": "books.md",
  "appended_content": "\n- The Expanse\n",
  "message": "Successfully appended to 'books.md'."
}
```

**Example usage:**
- `append_to_note("__INBOX.md", "Order furnace filters")` — timestamped capture to inbox
- `append_to_note("books.md", "- The Expanse", false)` — add a list item without a heading
- `append_to_note("bands.md", "- Khruangbin", false)` — creates the file if it doesn't exist yet

---

## Writable Notes Whitelist

Write access is intentionally limited to a small hardcoded list in [src/obsidian_mcp/vault.py](src/obsidian_mcp/vault.py):

```python
WRITABLE_NOTES = {
    "__INBOX.md":  "Quick capture inbox",
    "__scratch.md":"Temporary notes and thoughts",
    "bands.md":    "Music to check out",
    "books.md":    "Reading list",
}
```

To add or remove entries, edit that dict directly in source — the whitelist is deliberately not configurable via environment variables. All writable notes must live in the vault root (no subfolders).

---

### `list_templates`

List all `.md` files in your vault's `templates/` directory. Use this before `create_note_from_template` to see what's available.

**Input:** none

**Example result:**
```json
{
  "templates": [
    { "name": "PROJECT",       "path": "templates/PROJECT.md",       "size": 100, "description": "General project template" },
    { "name": "WRITING PROJECT","path": "templates/WRITING PROJECT.md","size": 96,  "description": "Writing project template" },
    { "name": "New Book",      "path": "templates/New Book.md",      "size": 87,  "description": "Book tracking template" }
  ]
}
```

Descriptions are extracted from the first line of each template if it's a comment (`%% ... %%` or `<!-- ... -->`), otherwise shown as "Template".

---

### `create_note_from_template`

Create a new note at the vault root from a named template. The file is named `{template_name} {note_suffix}.md`. If no suffix is given, a timestamp is used instead.

**Input:**
- `template_name` (string, required) — name of the template, e.g. `"PROJECT"` or `"New Book"`
- `note_suffix` (string, optional) — appended to the filename, e.g. `"deck replacement"` → `"PROJECT deck replacement.md"`. Letters, numbers, spaces, hyphens, underscores only.
- `field_values` (object, optional) — pre-fill template placeholders. Keys match `# KEY:` headings in the template.

**Example result:**
```json
{
  "success": true,
  "file_path": "PROJECT deck replacement.md",
  "message": "Created new note from template",
  "template_used": "templates/PROJECT.md"
}
```

**Example usage:**
```
create_note_from_template("PROJECT", "replacing the deck")
→ Creates "PROJECT replacing the deck.md"

create_note_from_template("New Book", "The Expanse")
→ Creates "New Book The Expanse.md"

create_note_from_template("PROJECT", "kitchen remodel", {"NEXT ACTION": "get contractor quotes"})
→ Creates "PROJECT kitchen remodel.md" with NEXT ACTION pre-filled
```

---

## Templates

The template system auto-discovers any `.md` file in your vault's `templates/` directory — no configuration needed. To add a new template type, just drop a file in there:

```
templates/
├── PROJECT.md
├── WRITING PROJECT.md
├── New Book.md
├── RECIPE.md          ← add your own
└── CODE_REVIEW.md     ← add your own
```

Adding an optional description comment at the top of a template makes it show up in `list_templates` output:

```markdown
%% My custom template for tracking recipes %%

# RECIPE NAME:

## Ingredients

## Steps

# NEXT ACTION:
```

Notes are always created in the vault root. Template names and note suffixes are restricted to letters, numbers, spaces, hyphens, and underscores — no path separators allowed.

### Template Placeholders

The following `{{PLACEHOLDER}}` tokens are automatically replaced when a note is created:

| Placeholder | Example output |
|---|---|
| `{{TODAY}}` | `2026-02-26` |
| `{{DATE}}` | `2026-02-26` (alias for TODAY) |
| `{{NOW}}` | `2026-02-26 15:30:45` |
| `{{TIME}}` | `15:30:45` |
| `{{TIMESTAMP}}` | `1740578445` (Unix timestamp) |
| `{{YEAR}}` | `2026` |
| `{{MONTH}}` | `02` |
| `{{DAY}}` | `26` |

Example template using placeholders:

```markdown
%% Book tracking template %%
---
date: "{{TODAY}}"
---

# TITLE:

# AUTHOR:

# NEXT ACTION:
```

When created, `date: "{{TODAY}}"` becomes `date: "2026-02-26"` automatically. Placeholders are expanded before any `field_values` are applied, so caller-supplied values always take precedence.
