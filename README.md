# obsidian-mcp

A stdio MCP server that provides read-only access to an Obsidian vault for LLM querying.

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

The server communicates over stdio and is meant to be launched by an MCP host (e.g. MstyStudio).

## MstyStudio Configuration

Add the following to your MstyStudio MCP servers config:

```json
{
  "mcpServers": {
    "obsidian": {
      "command": "python",
      "args": ["-m", "obsidian_mcp.server"],
      "env": {
        "VAULT_PATH": "/path/to/your/vault"
      }
    }
  }
}
```

> If you installed into a virtualenv, use the full path to that Python binary, e.g.
> `"/path/to/obsidian-mcp/.venv/bin/python"`.

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
