"""Obsidian MCP server - vault access via stdio transport."""

from __future__ import annotations

import os
from typing import Any

import mcp.server.stdio
import mcp.types as types
from dotenv import load_dotenv
from mcp.server import Server

from .vault import (
    append_to_note,
    create_note_from_template,
    get_note,
    list_notes,
    list_templates,
    list_writable_notes,
    search_notes,
)

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
        types.Tool(
            name="list_writable_notes",
            description="Show which notes support write (append) operations and whether they currently exist.",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        types.Tool(
            name="append_to_note",
            description=(
                "Append content to the end of a whitelisted note. "
                "Only notes returned by list_writable_notes can be written to. "
                "Use list_writable_notes first if unsure which notes are available."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "note_path": {
                        "type": "string",
                        "description": "Filename of the writable note (e.g. 'books.md'). Must be in the whitelist.",
                    },
                    "content": {
                        "type": "string",
                        "description": "Text to append to the note.",
                    },
                    "add_timestamp": {
                        "type": "boolean",
                        "description": "If true (default), prepend a '## YYYY-MM-DD HH:MM' heading before the content.",
                    },
                },
                "required": ["note_path", "content"],
            },
        ),
        types.Tool(
            name="list_templates",
            description=(
                "List all available templates in the vault's templates/ directory. "
                "Use this before create_note_from_template to see what templates exist."
            ),
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        types.Tool(
            name="create_note_from_template",
            description=(
                "Create a new note at the vault root from an existing template. "
                "The note is named '{template_name} {note_suffix}.md'. "
                "Use list_templates first to see available templates."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "template_name": {
                        "type": "string",
                        "description": "Name of the template to use (e.g. 'PROJECT', 'New Book'). Must match a file in templates/.",
                    },
                    "note_suffix": {
                        "type": "string",
                        "description": "Custom name to append after the template name (e.g. 'deck replacement'). Letters, numbers, spaces, hyphens, underscores only. If omitted, a timestamp is used.",
                    },
                    "field_values": {
                        "type": "object",
                        "description": "Optional key-value pairs to pre-fill the note. Keys should match YAML frontmatter field names in the template (e.g. {'title': 'My Book', 'authors': 'Jane Smith'}). Keys not found in frontmatter will be matched against '# KEY:' headings in the body instead.",
                        "additionalProperties": {"type": "string"},
                    },
                },
                "required": ["template_name"],
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

        elif name == "list_writable_notes":
            result = list_writable_notes(vault)
            import json
            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "append_to_note":
            note_path = arguments.get("note_path", "")
            content = arguments.get("content", "")
            if not note_path:
                raise ValueError("'note_path' argument is required")
            if not content:
                raise ValueError("'content' argument is required")
            add_timestamp = arguments.get("add_timestamp", True)
            result = append_to_note(vault, note_path, content, add_timestamp)
            import json
            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "list_templates":
            result = list_templates(vault)
            import json
            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "create_note_from_template":
            template_name = arguments.get("template_name", "")
            if not template_name:
                raise ValueError("'template_name' argument is required")
            note_suffix = arguments.get("note_suffix") or None
            field_values = arguments.get("field_values") or None
            import sys, json
            print(
                f"[create_note_from_template] template={template_name!r} "
                f"suffix={note_suffix!r} field_values={field_values!r}",
                file=sys.stderr,
            )
            result = create_note_from_template(vault, template_name, note_suffix, field_values)
            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

        else:
            raise ValueError(f"Unknown tool: {name}")

    except (FileNotFoundError, IsADirectoryError, NotADirectoryError, FileExistsError) as e:
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
