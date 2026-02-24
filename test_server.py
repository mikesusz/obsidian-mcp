"""
Quick test harness for the obsidian-mcp server.

Spawns the server as a subprocess over stdio (exactly how MstyStudio would)
and exercises each tool, printing the raw results.

Usage:
    python test_server.py [--vault /path/to/vault] [--note "relative/path.md"] [--query "search term"]

Defaults: reads VAULT_PATH from .env / environment, uses first note found for get_note.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

load_dotenv()

# ── helpers ──────────────────────────────────────────────────────────────────

RESET  = "\033[0m"
BOLD   = "\033[1m"
GREEN  = "\033[32m"
YELLOW = "\033[33m"
RED    = "\033[31m"
CYAN   = "\033[36m"


def header(msg: str) -> None:
    print(f"\n{BOLD}{CYAN}{'─' * 60}{RESET}")
    print(f"{BOLD}{CYAN}{msg}{RESET}")
    print(f"{BOLD}{CYAN}{'─' * 60}{RESET}")


def ok(msg: str) -> None:
    print(f"{GREEN}✓ {msg}{RESET}")


def warn(msg: str) -> None:
    print(f"{YELLOW}⚠ {msg}{RESET}")


def err(msg: str) -> None:
    print(f"{RED}✗ {msg}{RESET}")


def pretty(data: str) -> None:
    try:
        parsed = json.loads(data)
        print(json.dumps(parsed, indent=2))
    except json.JSONDecodeError:
        print(data)


# ── core ─────────────────────────────────────────────────────────────────────

async def run_tests(vault_path: str, note_path: str | None, query: str) -> None:
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "obsidian_mcp.server"],
        env={**os.environ, "VAULT_PATH": vault_path},
    )

    print(f"{BOLD}Vault:{RESET} {vault_path}")
    print(f"{BOLD}Server:{RESET} {sys.executable} -m obsidian_mcp.server")

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:

            # ── initialize ────────────────────────────────────────────────
            header("initialize")
            result = await session.initialize()
            ok(f"Connected — server: {result.serverInfo.name} {result.serverInfo.version or ''}")

            # ── list_tools ────────────────────────────────────────────────
            header("list_tools")
            tools_result = await session.list_tools()
            tools = tools_result.tools
            tool_names = [t.name for t in tools]
            ok(f"Tools advertised: {tool_names}")

            expected = {"search_notes", "get_note", "list_notes"}
            missing = expected - set(tool_names)
            if missing:
                err(f"Missing expected tools: {missing}")
            else:
                ok("All expected tools present")

            # ── list_notes (no folder) ────────────────────────────────────
            header("list_notes  (no folder)")
            r = await session.call_tool("list_notes", {})
            text = r.content[0].text if r.content else ""
            if r.isError:
                err(f"Tool returned error:\n{text}")
            else:
                try:
                    notes = json.loads(text)
                    ok(f"Found {len(notes)} note(s)")
                    if notes:
                        print(f"  First 3: {[n['path'] for n in notes[:3]]}")
                        if note_path is None:
                            note_path = notes[0]["path"]
                            warn(f"No --note given; will use first note: {note_path}")
                except json.JSONDecodeError:
                    warn(f"Response is not JSON:\n{text}")

            # ── list_notes (with folder) ──────────────────────────────────
            # Try the parent folder of the first note, or "." equivalent
            if note_path:
                folder = str(Path(note_path).parent) if Path(note_path).parent != Path(".") else None
                if folder:
                    header(f"list_notes  (folder={folder!r})")
                    r = await session.call_tool("list_notes", {"folder": folder})
                    text = r.content[0].text if r.content else ""
                    if r.isError:
                        err(f"Tool returned error:\n{text}")
                    else:
                        try:
                            notes = json.loads(text)
                            ok(f"Found {len(notes)} note(s) in '{folder}'")
                        except json.JSONDecodeError:
                            warn(f"Response is not JSON:\n{text}")

            # ── list_notes (bad folder) ───────────────────────────────────
            header("list_notes  (non-existent folder — expect error)")
            r = await session.call_tool("list_notes", {"folder": "__no_such_folder__"})
            text = r.content[0].text if r.content else ""
            if text.startswith("Error:"):
                ok(f"Returned expected error: {text}")
            else:
                warn(f"Expected an error message, got:\n{text}")

            # ── get_note ──────────────────────────────────────────────────
            if note_path:
                header(f"get_note  (path={note_path!r})")
                r = await session.call_tool("get_note", {"note_path": note_path})
                text = r.content[0].text if r.content else ""
                if r.isError:
                    err(f"Tool returned error:\n{text}")
                else:
                    try:
                        note = json.loads(text)
                        ok(f"Got note: {note.get('title')!r}  ({note.get('size')} bytes)")
                        print(f"  Frontmatter keys: {list(note.get('frontmatter', {}).keys())}")
                        preview = note.get("content", "")[:120].replace("\n", " ")
                        print(f"  Content preview: {preview!r}")
                    except json.JSONDecodeError:
                        warn(f"Response is not JSON:\n{text}")

            # ── get_note (missing file) ───────────────────────────────────
            header("get_note  (missing file — expect error)")
            r = await session.call_tool("get_note", {"note_path": "__nonexistent__.md"})
            text = r.content[0].text if r.content else ""
            if text.startswith("Error:"):
                ok(f"Returned expected error: {text}")
            else:
                warn(f"Expected an error message, got:\n{text}")

            # ── search_notes ──────────────────────────────────────────────
            header(f"search_notes  (query={query!r})")
            r = await session.call_tool("search_notes", {"query": query})
            text = r.content[0].text if r.content else ""
            if r.isError:
                err(f"Tool returned error:\n{text}")
            else:
                try:
                    results = json.loads(text)
                    ok(f"Search returned {len(results)} result(s)")
                    for res in results[:3]:
                        print(f"  [{res['relevance_score']}] {res['path']}")
                        print(f"    {res['snippet'][:80]}")
                except json.JSONDecodeError:
                    warn(f"Response is not JSON:\n{text}")

            # ── search_notes (no results) ─────────────────────────────────
            header("search_notes  (query unlikely to match anything)")
            r = await session.call_tool("search_notes", {"query": "zzzzzzzzzzzzzzzzzzzzzz"})
            text = r.content[0].text if r.content else ""
            if r.isError:
                err(f"Tool returned error:\n{text}")
            else:
                try:
                    results = json.loads(text)
                    ok(f"Returned {len(results)} result(s) (expected 0)")
                except json.JSONDecodeError:
                    warn(f"Response is not JSON:\n{text}")

    header("done")
    ok("Server exited cleanly")


def main() -> None:
    parser = argparse.ArgumentParser(description="Test harness for obsidian-mcp")
    parser.add_argument("--vault", help="Path to Obsidian vault (overrides VAULT_PATH env)")
    parser.add_argument("--note", help="Relative path to a note to test get_note with")
    parser.add_argument("--query", default="the", help="Search term for search_notes (default: 'the')")
    args = parser.parse_args()

    vault = args.vault or os.environ.get("VAULT_PATH", "")
    if not vault:
        err("No vault path. Set VAULT_PATH in .env or pass --vault /path/to/vault")
        sys.exit(1)

    asyncio.run(run_tests(vault, args.note, args.query))


if __name__ == "__main__":
    main()
