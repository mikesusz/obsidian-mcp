"""Read-only operations for an Obsidian vault."""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import TypedDict

import frontmatter


IGNORED_DIRS = {".obsidian"}


class NoteInfo(TypedDict):
    title: str
    path: str
    size: int
    modified: str


class NoteContent(TypedDict):
    title: str
    path: str
    content: str
    frontmatter: dict
    modified: str
    size: int


class SearchResult(TypedDict):
    title: str
    path: str
    snippet: str
    relevance_score: float


def _resolve_vault(vault_path: str) -> Path:
    """Resolve vault path, handling iCloud-style .nosync or spaces."""
    path = Path(vault_path).expanduser().resolve()
    if not path.exists():
        raise FileNotFoundError(f"Vault path does not exist: {path}")
    if not path.is_dir():
        raise NotADirectoryError(f"Vault path is not a directory: {path}")
    return path


def _is_ignored(path: Path, vault_root: Path) -> bool:
    """Return True if any path component is in IGNORED_DIRS."""
    try:
        relative = path.relative_to(vault_root)
    except ValueError:
        return True
    return any(part in IGNORED_DIRS for part in relative.parts)


def _format_modified(path: Path) -> str:
    return datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="seconds")


def _note_title(path: Path) -> str:
    return path.stem


def _relative_str(path: Path, vault_root: Path) -> str:
    return str(path.relative_to(vault_root))


def list_notes(vault_path: str, folder: str | None = None) -> list[NoteInfo]:
    """List all .md notes in the vault, optionally filtered by subfolder."""
    root = _resolve_vault(vault_path)
    search_root = root

    if folder:
        search_root = (root / folder).resolve()
        if not search_root.exists():
            raise FileNotFoundError(f"Folder not found: {folder}")
        if not search_root.is_relative_to(root):
            raise ValueError("Folder path escapes vault root")

    notes: list[NoteInfo] = []
    for md_file in sorted(search_root.rglob("*.md")):
        if _is_ignored(md_file, root):
            continue
        stat = md_file.stat()
        notes.append(
            NoteInfo(
                title=_note_title(md_file),
                path=_relative_str(md_file, root),
                size=stat.st_size,
                modified=_format_modified(md_file),
            )
        )
    return notes


def get_note(vault_path: str, note_path: str) -> NoteContent:
    """Retrieve full content and metadata for a note."""
    root = _resolve_vault(vault_path)
    full_path = (root / note_path).resolve()

    if not full_path.is_relative_to(root):
        raise ValueError("note_path escapes vault root")
    if not full_path.exists():
        raise FileNotFoundError(f"Note not found: {note_path}")
    if not full_path.is_file():
        raise IsADirectoryError(f"Path is a directory, not a note: {note_path}")
    if full_path.suffix.lower() != ".md":
        raise ValueError(f"Not a markdown file: {note_path}")
    if _is_ignored(full_path, root):
        raise PermissionError(f"Note is in an ignored directory: {note_path}")

    post = frontmatter.load(str(full_path))
    stat = full_path.stat()

    return NoteContent(
        title=_note_title(full_path),
        path=_relative_str(full_path, root),
        content=post.content,
        frontmatter=dict(post.metadata),
        modified=_format_modified(full_path),
        size=stat.st_size,
    )


def _build_snippet(text: str, query: str, context: int = 75) -> str:
    """Return a snippet of ~2*context chars around the first match."""
    lower_text = text.lower()
    lower_query = query.lower()
    idx = lower_text.find(lower_query)
    if idx == -1:
        return text[:context * 2].strip()
    start = max(0, idx - context)
    end = min(len(text), idx + len(query) + context)
    snippet = text[start:end].strip()
    if start > 0:
        snippet = "…" + snippet
    if end < len(text):
        snippet = snippet + "…"
    return snippet


def _score(title: str, content: str, query: str) -> float:
    """Simple relevance score: title match > content match, weighted by frequency."""
    q = query.lower()
    title_hits = title.lower().count(q)
    content_hits = content.lower().count(q)
    return title_hits * 5.0 + content_hits * 1.0


def search_notes(vault_path: str, query: str, limit: int = 10) -> list[SearchResult]:
    """Search notes by filename and content (case-insensitive), return top results."""
    root = _resolve_vault(vault_path)
    query_lower = query.lower()
    results: list[SearchResult] = []

    for md_file in root.rglob("*.md"):
        if _is_ignored(md_file, root):
            continue

        title = _note_title(md_file)
        try:
            raw_text = md_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        post = frontmatter.loads(raw_text)
        content = post.content

        title_match = query_lower in title.lower()
        content_match = query_lower in content.lower()

        if not (title_match or content_match):
            continue

        score = _score(title, content, query)
        snippet_source = content if content_match else title
        snippet = _build_snippet(snippet_source, query)

        results.append(
            SearchResult(
                title=title,
                path=_relative_str(md_file, root),
                snippet=snippet,
                relevance_score=round(score, 2),
            )
        )

    results.sort(key=lambda r: r["relevance_score"], reverse=True)
    return results[:limit]
