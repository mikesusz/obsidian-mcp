**Phase 1 Spec (Read-Only):**

---

## Obsidian MCP Server - Phase 1: Read-Only Access

**Goal**: Create a stdio MCP server that provides read-only access to an Obsidian vault for LLM querying.

**Tech Stack:**
- Python with MCP SDK
- Stdio transport (for local MstyStudio integration)
- Environment variables for configuration

**Project Structure:**
```
obsidian-mcp/
├── pyproject.toml          # Python dependencies & project config
├── .env.example            # Template: VAULT_PATH=/path/to/vault
├── .gitignore              # Exclude .env, __pycache__, etc.
├── README.md               # Setup & MstyStudio config instructions
└── src/
    └── obsidian_mcp/
        ├── __init__.py
        ├── server.py       # Main MCP server implementation
        └── vault.py        # Vault read operations
```

**Environment Configuration:**
```env
# .env.example
VAULT_PATH=/path/to/obsidian/vault
```

**MCP Tools to Implement:**

1. **search_notes**
   - Description: Search notes by content or title (case-insensitive)
   - Input: `query` (string, required)
   - Returns: Array of matches with context
   - Format: `[{title: str, path: str, snippet: str, relevance_score: float}]`
   - Implementation notes:
     - Search both filename and content
     - Return 50-100 char snippets around matches
     - Limit to top 10 results
     - Ignore `.obsidian/` folder

2. **get_note**
   - Description: Retrieve full content of a specific note
   - Input: `note_path` (string, required - relative to vault root)
   - Returns: Full note content with metadata
   - Format: `{title: str, path: str, content: str, frontmatter: dict, modified: str, size: int}`
   - Error handling: Return clear error if file doesn't exist

3. **list_notes**
   - Description: List all markdown notes in vault
   - Input: `folder` (string, optional - filter by subfolder)
   - Returns: Directory listing with metadata
   - Format: `[{title: str, path: str, size: int, modified: str}]`
   - Sort alphabetically by path

**Technical Requirements:**
- Only process `.md` files
- Parse frontmatter if present (use `python-frontmatter`)
- Ignore `.obsidian/` configuration folder
- Handle iCloud sync paths gracefully
- Proper error handling for file access issues
- Type hints throughout
- Async/await pattern for MCP handlers

**Dependencies (pyproject.toml):**
```toml
[project]
name = "obsidian-mcp"
version = "0.1.0"
dependencies = [
    "mcp",
    "python-dotenv",
    "python-frontmatter",
]
```

**README Requirements:**
- Installation instructions
- `.env` setup
- MstyStudio configuration example
- Example queries to test each tool

**MstyStudio Config Example for README:**
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

---
