"""Vault operations for an Obsidian vault (read + controlled write)."""

from __future__ import annotations

import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import TypedDict

import frontmatter


IGNORED_DIRS = {".obsidian"}

# Hardcoded whitelist of notes that support write operations.
# All paths are relative to the vault root and must be in the root (no subfolders).
# To add a new writable note, edit this dict in source.
WRITABLE_NOTES: dict[str, str] = {
    "__INBOX.md": "Quick capture inbox",
    "__scratch.md": "Temporary notes and thoughts",
    "bands.md": "Music to check out",
    "books.md": "Reading list",
}


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


# ── write operations ──────────────────────────────────────────────────────────

class WritableNoteInfo(TypedDict):
    path: str
    exists: bool
    purpose: str


class AppendResult(TypedDict):
    success: bool
    note_path: str
    appended_content: str
    message: str


def list_writable_notes(vault_path: str) -> dict[str, list[WritableNoteInfo]]:
    """Return the whitelist of writable notes with existence status."""
    root = _resolve_vault(vault_path)
    notes = [
        WritableNoteInfo(
            path=note_path,
            exists=(root / note_path).exists(),
            purpose=purpose,
        )
        for note_path, purpose in WRITABLE_NOTES.items()
    ]
    return {"writable_notes": notes}


def append_to_note(
    vault_path: str,
    note_path: str,
    content: str,
    add_timestamp: bool = True,
) -> AppendResult:
    """Append content to a whitelisted note, optionally prefixed with a timestamp heading."""
    # Safety: exact whitelist lookup — also implicitly blocks path traversal
    # because traversal strings like "../etc/passwd" are simply not in the dict.
    if note_path not in WRITABLE_NOTES:
        raise PermissionError(
            f"'{note_path}' is not in the writable whitelist. "
            f"Writable notes: {list(WRITABLE_NOTES)}"
        )

    # Belt-and-suspenders: reject anything with a path separator even if
    # someone somehow extended WRITABLE_NOTES with a subfolder entry.
    if "/" in note_path or "\\" in note_path:
        raise ValueError("note_path must be a filename, not a path")

    root = _resolve_vault(vault_path)
    full_path = root / note_path

    if add_timestamp:
        ts = datetime.now().strftime("%Y-%m-%d %H:%M")
        block = f"\n## {ts}\n{content}\n"
    else:
        block = f"\n{content}\n"

    created = not full_path.exists()

    if not created:
        existing = full_path.read_text(encoding="utf-8")
        if existing and not existing.endswith("\n"):
            block = "\n" + block

    with full_path.open("a", encoding="utf-8") as f:
        f.write(block)

    # Log to stderr so it doesn't interfere with the stdio MCP transport
    ts_log = datetime.now().isoformat(timespec="seconds")
    action = "created+appended" if created else "appended"
    print(f"[{ts_log}] write: {action} {note_path!r}", file=sys.stderr)

    msg = (
        f"Created '{note_path}' and appended content."
        if created
        else f"Successfully appended to '{note_path}'."
    )

    return AppendResult(
        success=True,
        note_path=note_path,
        appended_content=block,
        message=msg,
    )


# ── template operations ───────────────────────────────────────────────────────

# Allowed characters in template names and note suffixes.
# Covers the examples in the spec: "PROJECT", "WRITING PROJECT", "New Book", etc.
_SAFE_NAME_RE = re.compile(r"^[a-zA-Z0-9 _-]+$")
_MAX_FILENAME_LEN = 200


class TemplateInfo(TypedDict):
    name: str
    path: str
    size: int
    description: str


class CreateNoteResult(TypedDict):
    success: bool
    file_path: str
    message: str
    template_used: str
    fields_applied: dict[str, str]


def _replace_placeholders(content: str) -> str:
    """Replace {{PLACEHOLDER}} tokens with current date/time values."""
    now = datetime.now()
    replacements = {
        "{{TODAY}}":     now.strftime("%Y-%m-%d"),
        "{{DATE}}":      now.strftime("%Y-%m-%d"),
        "{{NOW}}":       now.strftime("%Y-%m-%d %H:%M:%S"),
        "{{TIME}}":      now.strftime("%H:%M:%S"),
        "{{TIMESTAMP}}": str(int(now.timestamp())),
        "{{YEAR}}":      now.strftime("%Y"),
        "{{MONTH}}":     now.strftime("%m"),
        "{{DAY}}":       now.strftime("%d"),
    }
    for placeholder, value in replacements.items():
        content = content.replace(placeholder, value)
    return content


def _extract_template_description(content: str) -> str:
    """Pull a description from the first line if it's a comment, otherwise generic."""
    first_line = content.lstrip().split("\n")[0] if content.strip() else ""
    # Obsidian block comment: %% some description %%
    if first_line.startswith("%%"):
        inner = first_line.strip("%").strip()
        if inner:
            return inner
    # HTML comment: <!-- some description -->
    if first_line.startswith("<!--"):
        inner = re.sub(r"^<!--\s*|-->.*$", "", first_line).strip()
        if inner:
            return inner
    return "Template"


def _validate_safe_name(value: str, label: str) -> None:
    """Raise ValueError if value contains characters outside the safe set."""
    if not value:
        raise ValueError(f"{label} must not be empty")
    if not _SAFE_NAME_RE.match(value):
        raise ValueError(
            f"{label} contains invalid characters — "
            "only letters, numbers, spaces, hyphens, and underscores are allowed"
        )


def _templates_dir(root: Path) -> Path:
    td = root / "templates"
    if not td.exists() or not td.is_dir():
        raise FileNotFoundError("Templates directory not found in vault")
    return td


def list_templates(vault_path: str) -> dict[str, list[TemplateInfo]]:
    """List all .md files in the vault's templates/ directory."""
    root = _resolve_vault(vault_path)
    td = _templates_dir(root)

    templates: list[TemplateInfo] = []
    for md_file in sorted(td.glob("*.md")):
        try:
            content = md_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            content = ""
        stat = md_file.stat()
        templates.append(
            TemplateInfo(
                name=md_file.stem,
                path=_relative_str(md_file, root),
                size=stat.st_size,
                description=_extract_template_description(content),
            )
        )
    return {"templates": templates}


def create_note_from_template(
    vault_path: str,
    template_name: str,
    note_suffix: str | None = None,
    field_values: dict[str, str] | None = None,
) -> CreateNoteResult:
    """Create a new note in the vault root from a named template."""
    _validate_safe_name(template_name, "Template name")

    root = _resolve_vault(vault_path)
    td = _templates_dir(root)

    template_path = td / f"{template_name}.md"
    if not template_path.exists():
        available = [f.stem for f in sorted(td.glob("*.md"))]
        available_str = ", ".join(available) if available else "none"
        raise FileNotFoundError(
            f"Template '{template_name}' not found. "
            f"Available templates: {available_str}"
        )

    # Build output filename
    if note_suffix and note_suffix.strip():
        _validate_safe_name(note_suffix.strip(), "Note suffix")
        filename = f"{template_name} {note_suffix.strip()}.md"
    else:
        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        filename = f"{template_name} {ts}.md"

    if len(filename) > _MAX_FILENAME_LEN:
        raise ValueError(f"Filename too long (max {_MAX_FILENAME_LEN} characters)")

    output_path = root / filename
    if output_path.exists():
        raise FileExistsError(f"Note already exists: {filename}")

    # Read template and apply field_values, then expand placeholders last.
    # field_values strategy:
    #   - Keys that match existing YAML frontmatter fields → update the frontmatter dict
    #   - Keys with no frontmatter match → fall back to # KEY: heading replacement in body
    # Placeholders ({{TODAY}} etc.) are expanded after all field substitution so they
    # are also resolved inside any freshly-written frontmatter values.
    raw = template_path.read_text(encoding="utf-8")

    applied: dict[str, str] = {}
    if field_values:
        post = frontmatter.loads(raw)
        body_replacements: dict[str, str] = {}
        for key, value in field_values.items():
            if key in post.metadata:
                if key == "authors" and isinstance(value, str) and " and " in value:
                    post.metadata[key] = [name.strip() for name in value.split(" and ")]
                else:
                    post.metadata[key] = value
                applied[key] = value
            else:
                body_replacements[key] = value
        content = frontmatter.dumps(post)
        for key, value in body_replacements.items():
            if f"# {key}:" in content:
                content = content.replace(f"# {key}:", f"# {key}:\n{value}")
                applied[key] = value
    else:
        content = raw

    content = _replace_placeholders(content)

    output_path.write_text(content, encoding="utf-8")

    ts_log = datetime.now().isoformat(timespec="seconds")
    print(
        f"[{ts_log}] create: '{filename}' from template '{template_name}' "
        f"fields_applied={list(applied)}",
        file=sys.stderr,
    )

    return CreateNoteResult(
        success=True,
        file_path=filename,
        message="Created new note from template",
        template_used=_relative_str(template_path, root),
        fields_applied=applied,
    )
