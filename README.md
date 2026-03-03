# obsidian-mcp

A stdio MCP server that gives LLMs read and (limited) write access to an Obsidian vault. Full read access to all notes; append-only write access to a configurable list of notes; and structured note creation from templates.

## Quick Start

```bash
# 1. Clone and install
git clone https://github.com/your-username/obsidian-mcp
cd obsidian-mcp
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e .

# 2. Set your vault path
cp .env.example .env
# Edit .env and set VAULT_PATH=/path/to/your/vault

# 3. (Optional) Configure writable notes
cp .obsidian-mcp.config.example.json /path/to/your/vault/.obsidian-mcp.config.json
# Edit to match your vault

# 4. Add to your MCP client (see MCP Client Configuration below)
```

## Requirements

- Python 3.10+
- An Obsidian vault on your local filesystem

## Installation

```bash
git clone https://github.com/your-username/obsidian-mcp
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

### Writable notes

By default, only `__INBOX.md` and `__scratch.md` can be written to. To customize this, copy the example config into your vault root:

```bash
cp .obsidian-mcp.config.example.json /path/to/your/vault/.obsidian-mcp.config.json
```

Edit it to list whichever notes you want to be writable:

```json
{
	"writable_notes": [
		{ "path": "__INBOX.md", "description": "Quick capture inbox" },
		{ "path": "__scratch.md", "description": "Temporary scratch pad" },
		{ "path": "books.md", "description": "Reading list" }
	]
}
```

All writable notes must be in the vault root (no subfolders). The config is read on every request, so changes take effect immediately without restarting the server.

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

- `JOURNAL.md` — Daily journal with date auto-filled
- `RECIPE.md` — Recipe with source and ingredients
- `MEETING_NOTES.md` — Meeting notes with attendees array

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

Placeholders are expanded after `field_values` are applied, so caller-supplied values always take precedence.

### Array fields

If a `field_values` value for an array-typed frontmatter field contains `and`, it's automatically split into a list:

```
"William Gibson and Bruce Sterling" → ["William Gibson", "Bruce Sterling"]
```

This lets you answer natural-language questions ("who are the authors?") and still get correctly structured YAML.

---

## Writable Notes

Write access is limited to notes explicitly listed in `.obsidian-mcp.config.json` in your vault root (see [Configuration](#writable-notes)). If no config file is present, only `__INBOX.md` and `__scratch.md` are writable by default.

All writable notes must be in the vault root (no subfolders). Path traversal protection is structural: only filenames explicitly listed in the config can be written to, so `../etc/passwd`-style paths are blocked by design.

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
