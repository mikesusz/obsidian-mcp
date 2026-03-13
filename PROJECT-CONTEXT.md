# obsidian-mcp — Project Context

A Python-based MCP (Model Context Protocol) server that gives LLMs read and limited write access to an Obsidian vault over stdio. Designed for use with Claude Desktop and other MCP-compatible clients.

## What It Does

- **Full read access** to all markdown notes in a vault (search, retrieve, list)
- **Append-only write access** to a configurable whitelist of notes
- **Template-based note creation** with field substitution and date/time placeholders
- All configured via environment variable (`VAULT_PATH`) and an optional JSON config file in the vault root

## Tech Stack

- Python 3.10+, async/await throughout
- `mcp` — MCP SDK (stdio transport)
- `python-frontmatter` — YAML frontmatter parsing
- `python-dotenv` — env var management
- `hatchling` — build backend

## Architecture

```
src/obsidian_mcp/
  server.py     — MCP server entry point; registers and routes all 7 tools
  vault.py      — All vault I/O: reading, searching, writing, template expansion

templates/
  examples/     — JOURNAL.md, RECIPE.md, MEETING_NOTES.md starter templates

test_server.py  — End-to-end test harness; spawns server as subprocess over stdio
```

## The 7 MCP Tools

### Read
| Tool | Description |
|------|-------------|
| `list_notes` | List all `.md` files; optional subfolder filter |
| `get_note` | Full content + frontmatter + metadata for a specific note |
| `search_notes` | Case-insensitive search of titles and content; returns up to 10 scored results with snippets |

### Write
| Tool | Description |
|------|-------------|
| `list_writable_notes` | Show which notes are whitelisted for writing (from config or defaults) |
| `append_to_note` | Append content to a whitelisted note; optionally prefixes with a timestamp heading; creates file if missing |

### Templates
| Tool | Description |
|------|-------------|
| `list_templates` | Discover all `.md` files under vault's `templates/` dir; extracts description from first-line comment |
| `create_note_from_template` | Create a new note from a template; substitutes frontmatter fields, `# KEY:` body patterns, and `{{PLACEHOLDER}}` tokens |

## Template Placeholders

`{{TODAY}}`, `{{DATE}}`, `{{NOW}}`, `{{TIME}}`, `{{TIMESTAMP}}`, `{{YEAR}}`, `{{MONTH}}`, `{{DAY}}`

## Configuration

**`.env`** (gitignored):
```
VAULT_PATH=/path/to/your/vault
```

**`.obsidian-mcp.config.json`** (vault root, gitignored) — controls writable notes whitelist:
```json
{
  "writable_notes": [
    { "path": "__INBOX.md",  "purpose": "Quick capture inbox" },
    { "path": "__scratch.md", "purpose": "Scratch pad" }
  ]
}
```
Defaults to `__INBOX.md` and `__scratch.md` if no config file is present.

## Safety Model

- **Reads:** All `.md` files accessible; `.obsidian/` directory skipped; path traversal rejected
- **Writes:** Whitelist-only; append-only (never overwrites); vault-root-only (no subfolders); path traversal structurally impossible (whitelist lookup)
- **Template creation:** Safe filename validation (regex + 200 char max); duplicate protection; vault-root output only
- All write/create operations logged to stderr (doesn't interfere with stdio transport)

## How It Evolved

| Phase | What Was Built |
|-------|---------------|
| 1 | Read-only: `search_notes`, `get_note`, `list_notes` |
| 2 | Append-only writes: `append_to_note`, `list_writable_notes` |
| 2.5 | Template creation: `list_templates`, `create_note_from_template`, field substitution |
| 2.6 | Smart placeholders: `{{TODAY}}`, `{{NOW}}`, etc. |
| 3 | Config file abstraction, example templates, README, general-purpose release |

## Running

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e .
cp .env.example .env  # set VAULT_PATH

# Test against a real vault:
python test_server.py --vault /path/to/your/vault
```

## MCP Client Setup (Claude Desktop example)

```json
{
  "mcpServers": {
    "obsidian": {
      "command": "/path/to/obsidian-mcp/.venv/bin/python",
      "args": ["-m", "obsidian_mcp.server"],
      "env": { "VAULT_PATH": "/path/to/your/vault" }
    }
  }
}
```
