# obsidian-mcp

A stdio MCP server that gives LLMs controlled access to an Obsidian vault. Per-note permissions are set via `agent_access` frontmatter (`hidden`, `read`, `append`, `edit`). Append-only write access to a configurable inbox/scratch whitelist. Structured note creation from templates.

_Note:_ if you want a simple, read-only local Obsidian MCP Server, you can use the [1.0 Release of this project](https://github.com/mikesusz/obsidian-mcp/releases/tag/1.0), which includes no file-write capabilities whatsoever.

## Quick Start

```bash
# 1. Clone and install
git clone https://github.com/mikesusz/obsidian-mcp
cd obsidian-mcp
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e .

# 2. Set your vault path
cp .env.example .env
# Edit .env and set VAULT_PATH=/path/to/your/vault

# 3. (Optional) Configure append whitelist for inbox/scratch notes
cp .obsidian-mcp.config.example.json /path/to/your/vault/.obsidian-mcp.config.json
# Edit to match your vault — per-note permissions use agent_access frontmatter instead

# 4. Add to your MCP client (see MCP Client Configuration below)
```

## Requirements

- Python 3.10+
- An Obsidian vault on your local filesystem

## Installation

```bash
git clone https://github.com/mikesusz/obsidian-mcp
cd obsidian-mcp
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e .
```

## Configuration

### Vault path

Copy the example env file and set your vault path:

```bash
cp .env.example .env
```

Edit `.env`:

```env
VAULT_PATH=/path/to/your/obsidian/vault
```

### Per-note access control

Add an `agent_access` field to any note's frontmatter to control what the agent can do with it:

```yaml
---
agent_access: "hidden"   # invisible to the agent — won't appear in search or list
agent_access: "read"     # agent can read but not modify
agent_access: "append"   # agent can only add content (safe default)
agent_access: "edit"     # agent can freely edit
---
```

No config file needed — just add the field to the note. Notes without `agent_access` default to `append`.

### Append whitelist (inbox/scratch notes)

The `append_to_note` tool uses a separate whitelist for quick-capture notes like an inbox or scratch pad. By default, only `__INBOX.md` and `__scratch.md` are in this list. To customize it, copy the example config into your vault root:

```bash
cp .obsidian-mcp.config.example.json /path/to/your/vault/.obsidian-mcp.config.json
```

Edit it to list whichever notes you want available for appending:

```json
{
	"writable_notes": [
		{ "path": "__INBOX.md", "description": "Quick capture inbox" },
		{ "path": "__scratch.md", "description": "Temporary scratch pad" },
		{ "path": "books.md", "description": "Reading list" }
	]
}
```

All whitelist notes must be in the vault root (no subfolders). The config is read on every request, so changes take effect immediately without restarting the server.

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

## Running the server manually

```bash
python -m obsidian_mcp.server
# or
obsidian-mcp
```

The server communicates over stdio and is normally launched automatically by your MCP client.

---

## Available Tools

### `search_notes`

Search notes by title or content (case-insensitive). Returns up to 10 results with a short excerpt around each match.

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

---

### `list_notes`

List all markdown notes in the vault (or a subfolder).

**Input:**

- `folder` (string, optional) — subfolder path relative to vault root

**Example result:**

```json
[
	{ "title": "Home", "path": "Home.md", "size": 512, "modified": "2024-06-01T09:00:00" },
	{
		"title": "Daily Note",
		"path": "Daily/2024-01-15.md",
		"size": 256,
		"modified": "2024-01-15T08:00:00"
	}
]
```

---

### `list_writable_notes`

Show which notes support write (append) operations, and whether each one currently exists.

**Input:** none

**Example result:**

```json
{
	"writable_notes": [
		{ "path": "__INBOX.md", "exists": true, "purpose": "Quick capture inbox" },
		{ "path": "__scratch.md", "exists": true, "purpose": "Temporary scratch pad" },
		{ "path": "books.md", "exists": false, "purpose": "Reading list" }
	]
}
```

---

### `append_to_note`

Append content to the end of a writable note. Never overwrites existing content. Creates the file if it doesn't exist yet.

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

### `list_templates`

List all `.md` files in your vault's `templates/` directory.

**Input:** none

**Example result:**

```json
{
	"templates": [
		{
			"name": "PROJECT",
			"path": "templates/PROJECT.md",
			"size": 100,
			"description": "General project template"
		},
		{
			"name": "JOURNAL",
			"path": "templates/JOURNAL.md",
			"size": 96,
			"description": "Daily journal entry"
		},
		{
			"name": "New Book",
			"path": "templates/New Book.md",
			"size": 87,
			"description": "Book tracking template"
		}
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
- `field_values` (object, optional) — pre-fill template fields. Keys match YAML frontmatter field names (e.g. `{"title": "My Book", "authors": "Jane Smith"}`). Keys not found in frontmatter will be matched against `# KEY:` headings in the body instead.
- `agent_access` (string, optional) — permission level for agent access after creation: `"edit"`, `"append"` (default), `"read"`, or `"hidden"`. Overrides any value already in the template's `agent_access` frontmatter field. Infer from the user's phrasing (see [Agent access in templates](#agent-access-in-templates)).

**Example result:**

```json
{
	"success": true,
	"file_path": "PROJECT deck replacement.md",
	"message": "Created new note from template",
	"template_used": "templates/PROJECT.md",
	"fields_applied": { "title": "deck replacement" }
}
```

**Example usage:**

```
create_note_from_template("PROJECT", "replacing the deck")
→ Creates "PROJECT replacing the deck.md"

create_note_from_template("New Book", "The Expanse", {"title": "The Expanse", "authors": "James S.A. Corey"})
→ Creates "New Book The Expanse.md" with frontmatter populated

create_note_from_template("MEETING_NOTES", "Q1 planning", {"attendees": "Alice and Bob and Carol"})
→ Creates "MEETING_NOTES Q1 planning.md" with attendees: ["Alice", "Bob", "Carol"]

create_note_from_template("REFERENCE_DOC", "mechanical keyboards", agent_access="edit")
→ Creates "REFERENCE_DOC mechanical keyboards.md" with agent_access: "edit"
```

---

### `update_note`

Replace the entire body of a note with new content. Frontmatter (including `agent_access`) is always preserved. Requires `agent_access: "edit"` in the note.

**Input:**

- `note_path` (string, required) — filename relative to vault root, e.g. `"My Note.md"`
- `new_content` (string, required) — full replacement body text

**Example result:**

```json
{
  "success": true,
  "note_path": "REFERENCE_DOC mechanical keyboards.md",
  "message": "Note body updated: 'REFERENCE_DOC mechanical keyboards.md'"
}
```

---

### `replace_in_note`

Find and replace a specific piece of text in a note body. Exact match, case-sensitive. Only operates on body content — frontmatter is never touched. Requires `agent_access: "edit"`.

**Input:**

- `note_path` (string, required) — filename relative to vault root
- `old_text` (string, required) — exact text to find
- `new_text` (string, required) — replacement text

**Errors:**
- `"Text not found in note: '...'"` — if `old_text` doesn't appear in the body

---

### `update_section`

Replace the content beneath a specific heading, preserving the heading line itself. Content is replaced up to (but not including) the next heading, or end of file. Requires `agent_access: "edit"`.

**Input:**

- `note_path` (string, required) — filename relative to vault root
- `heading` (string, required) — exact heading text, e.g. `"## Next Steps"` or `"SYNOPSIS:"`
- `new_content` (string, required) — replacement content for that section

**Errors:**
- `"Heading '...' not found in note"` — if the heading doesn't exist

---

### Permission requirements

| Tool | Required `agent_access` |
| ---- | ----------------------- |
| `get_note`, `search_notes`, `list_notes` | `"read"` or higher (invisible if `"hidden"`) |
| `append_to_note` | whitelist-based (see [Writable Notes](#writable-notes)) |
| `update_note` | `"edit"` |
| `replace_in_note` | `"edit"` |
| `update_section` | `"edit"` |

If a note lacks the required `agent_access` value, all edit tools return:

```
Error: Insufficient permissions. This note has agent_access: 'append', but this operation requires: 'edit'. Add agent_access: 'edit' to the note's frontmatter to enable this operation.
```

---

## Templates

### Adding templates

Drop any `.md` file into your vault's `templates/` directory — no configuration needed:

```
templates/
├── PROJECT.md
├── New Book.md
├── JOURNAL.md
└── RECIPE.md
```

Add an optional description comment at the top to make it show up nicely in `list_templates`:

```markdown
%% My recipe template %%

---

date: "{{TODAY}}"
source: ""

---

# TITLE:

# SOURCE:

## Ingredients

## Steps
```

The `templates/examples/` directory in this repo contains ready-to-use templates you can copy into your vault:

- `JOURNAL.md` — Daily journal with date auto-filled (`agent_access: "append"`)
- `RECIPE.md` — Recipe with source and ingredients
- `MEETING_NOTES.md` — Meeting notes with attendees array (`agent_access: "edit"`)
- `REFERENCE_DOC.md` — Reference document with dynamic `agent_access` via `{{AGENT_ACCESS}}`

### Agent access in templates

Templates can include an `agent_access` frontmatter field to declare how freely an agent should edit the note after creation:

| Value | Meaning |
| ------- | ------- |
| `"edit"` | Agent can freely edit the note |
| `"append"` | Agent should only add content, not edit existing text (safe default) |
| `"read"` | Agent can view but not modify the note |
| `"hidden"` | Agent cannot see, search, or access this note at all |

**Hardcoded in template** (e.g. JOURNAL.md always appends):
```markdown
---
date: "{{TODAY}}"
agent_access: "append"
---
```

**Dynamic via placeholder** (e.g. REFERENCE_DOC.md — set at creation time):
```markdown
---
title: "{{TITLE}}"
agent_access: "{{AGENT_ACCESS}}"
---
```

When using the dynamic placeholder, pass `agent_access` to `create_note_from_template` and the value is inferred from the user's phrasing:

| User says… | Inferred value |
| --- | --- |
| "you can edit/update/modify" or "fully editable" | `"edit"` |
| "you can add to" or "append-only" | `"append"` |
| No specific instruction | `"append"` (safe default) |
| "read-only", "I'll edit this myself", "just create it" | `"read"` |
| "this is private", "keep this hidden", "don't show this" | `"hidden"` |

If `agent_access` is passed explicitly to `create_note_from_template`, it overrides whatever value the template has (hardcoded or placeholder).

### Template placeholders

The following `{{PLACEHOLDER}}` tokens are automatically replaced when a note is created:

| Placeholder     | Example output                 |
| --------------- | ------------------------------ |
| `{{TODAY}}`     | `2026-02-27`                   |
| `{{DATE}}`      | `2026-02-27` (alias for TODAY) |
| `{{NOW}}`       | `2026-02-27 15:30:45`          |
| `{{TIME}}`      | `15:30:45`                     |
| `{{TIMESTAMP}}` | `1740578445` (Unix timestamp)  |
| `{{YEAR}}`      | `2026`                         |
| `{{MONTH}}`     | `02`                           |
| `{{DAY}}`       | `27`                           |
| `{{AGENT_ACCESS}}` | `"append"` (resolved from the `agent_access` parameter, default `"append"`) |

Placeholders are expanded after `field_values` are applied, so caller-supplied values always take precedence.

### Array fields

If a `field_values` value for an array-typed frontmatter field contains `and`, it's automatically split into a list:

```
"William Gibson and Bruce Sterling" → ["William Gibson", "Bruce Sterling"]
```

This lets you answer natural-language questions ("who are the authors?") and still get correctly structured YAML.

---

## Access Control

**Per-note permissions** are set via `agent_access` in a note's frontmatter — no config file needed. Notes marked `hidden` are completely invisible to the agent; `read` notes can be viewed but not modified; `append` (default) allows adding content only; `edit` allows full modification.

**Append whitelist** (`append_to_note`) uses `.obsidian-mcp.config.json` in your vault root. If no config file is present, only `__INBOX.md` and `__scratch.md` are available. All whitelist notes must be in the vault root. Path traversal protection is structural: only filenames explicitly listed in the config can be written to, so `../etc/passwd`-style paths are blocked by design.

---

## Testing

Run the end-to-end test harness (requires a real vault):

```bash
python test_server.py --vault /path/to/your/vault
```

Options:

- `--vault` — path to vault (overrides `VAULT_PATH` env)
- `--note` — specific note path to test `get_note` with
- `--query` — search term for `search_notes` (default: `"the"`)

The harness spawns the server as a subprocess, exercises all 7 tools, and reports pass/fail for each. It also tests error cases: path traversal attempts, non-whitelisted writes, duplicate note creation, and invalid template names.

---

## Troubleshooting

**`VAULT_PATH environment variable is not set`**
Copy `.env.example` to `.env` and set the path, or pass `VAULT_PATH` in your MCP client config.

**`Templates directory not found in vault`**
Create a `templates/` folder in your vault root, or copy templates from `templates/examples/` in this repo.

**`'foo.md' is not in the writable whitelist`**
Add the note to `.obsidian-mcp.config.json` in your vault root (see [Writable notes](#writable-notes)).

**Changes to server code aren't taking effect**
Your MCP client keeps the server process alive. Restart the client (e.g. quit and relaunch Claude Desktop) to pick up code changes.

**`field_values` not updating frontmatter**
Check that the key names exactly match the YAML frontmatter keys in the template (case-sensitive). Use `fields_applied` in the response to confirm what was actually written.

## License

GNU Affero General Public License v3.0 — see [LICENSE](LICENSE) for the full text.

You are free to use, modify, and distribute this software under the AGPL v3 terms. If you run a modified version as a network service, you must make the modified source available to users of that service.

---

## Feedback

This project is a work in progress, and may have bugs. You can submit [a Github Issue](https://github.com/mikesusz/obsidian-mcp/issues) if you encounter any problems, and I will probably fix it! Because I don't want to have that problem, either.
