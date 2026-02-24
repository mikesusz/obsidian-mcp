"""Obsidian MCP server - read-only vault access via stdio transport."""

from __future__ import annotations

import os
from typing import Any

import mcp.server.stdio
import mcp.types as types
from dotenv import load_dotenv
from mcp.server import Server

from .vault import get_note, list_notes, search_notes

load_dotenv()

app = Server("obsidian-mcp")


def _vault_path() -> str:
    path = os.environ.get("VAULT_PATH", "")
    if not path:
        raise RuntimeError(
            "VAULT_PATH environment variable is not set. "
            "Copy .env.example to .env and set your vault path."
        )
    return path


@app.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="search_notes",
            description="Search notes by content or title (case-insensitive). Returns up to 10 matches with a short excerpt around each match.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search term to look for in note titles and content",
                    }
                },
                "required": ["query"],
            },
        ),
        types.Tool(
            name="get_note",
            description="Retrieve the full content and metadata of a specific note by its path relative to the vault root.",
            inputSchema={
                "type": "object",
                "properties": {
                    "note_path": {
                        "type": "string",
                        "description": "Path to the note relative to the vault root (e.g. 'folder/My Note.md')",
                    }
                },
                "required": ["note_path"],
            },
        ),
        types.Tool(
            name="list_notes",
            description="List all markdown notes in the vault, optionally filtered to a specific subfolder.",
            inputSchema={
                "type": "object",
                "properties": {
                    "folder": {
                        "type": "string",
                        "description": "Optional subfolder path relative to vault root to filter results",
                    }
                },
                "required": [],
            },
        ),
    ]


@app.call_tool()
async def handle_call_tool(
    name: str, arguments: dict[str, Any]
) -> list[types.TextContent]:
    try:
        vault = _vault_path()

        if name == "search_notes":
            query = arguments.get("query", "")
            if not query:
                raise ValueError("'query' argument is required")
            results = search_notes(vault, query)
            import json
            return [types.TextContent(type="text", text=json.dumps(results, indent=2))]

        elif name == "get_note":
            note_path = arguments.get("note_path", "")
            if not note_path:
                raise ValueError("'note_path' argument is required")
            result = get_note(vault, note_path)
            import json
            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "list_notes":
            folder = arguments.get("folder")
            results = list_notes(vault, folder)
            import json
            return [types.TextContent(type="text", text=json.dumps(results, indent=2))]

        else:
            raise ValueError(f"Unknown tool: {name}")

    except (FileNotFoundError, IsADirectoryError, NotADirectoryError) as e:
        return [types.TextContent(type="text", text=f"Error: {e}")]
    except (ValueError, PermissionError, RuntimeError) as e:
        return [types.TextContent(type="text", text=f"Error: {e}")]


async def _run() -> None:
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options(),
        )


def main() -> None:
    import asyncio
    asyncio.run(_run())


if __name__ == "__main__":
    main()
