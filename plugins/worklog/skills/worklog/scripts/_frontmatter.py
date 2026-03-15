"""Shared TOML frontmatter parsing, ID scanning, and field updates for worklog scripts."""

import re
import tomllib
from datetime import date
from pathlib import Path
from typing import NamedTuple


class ParsedDoc(NamedTuple):
    frontmatter: dict
    body: str


def split_frontmatter(text: str) -> ParsedDoc:
    """Split +++ delimited TOML frontmatter from body.

    Returns ParsedDoc(frontmatter, body). TOML-only — no YAML support.
    Raises ValueError if an unclosed frontmatter block is detected.
    """
    if text.startswith("+++\n"):
        m = re.match(r"^\+\+\+\n(.*?\n)\+\+\+\n?", text, re.DOTALL)
        if not m:
            raise ValueError("Unclosed frontmatter block (expected closing '+++')")
        return ParsedDoc(tomllib.loads(m.group(1)), text[m.end() :])
    return ParsedDoc({}, text)


def parse_item(path: Path | str) -> dict:
    """Read a worklog item file, return frontmatter dict with _path and _body."""
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    fm, body = split_frontmatter(text)
    fm["_path"] = path
    fm["_body"] = body
    return fm


_ID_RE = re.compile(r"^([tps])(\d{4})")

# Prefix patterns per item class
CLASS_PREFIX = {"task": "t", "plan": "p", "spec": "s"}


def iter_items(class_dir: Path, prefix: str) -> list[Path]:
    """Discover item files under class_dir, supporting both flat and directory formats.

    Flat:  {prefix}NNNN-kebab.md
    Dir:   {prefix}NNNN-kebab/index.md

    Returns sorted list of Path objects pointing to the .md file to parse.
    """
    if not class_dir.is_dir():
        return []
    pattern = re.compile(rf"^{re.escape(prefix)}\d{{4}}")
    results: list[Path] = []
    for entry in class_dir.iterdir():
        if entry.is_file() and entry.suffix == ".md" and pattern.match(entry.stem):
            results.append(entry)
        elif entry.is_dir() and pattern.match(entry.name):
            index = entry / "index.md"
            if index.exists():
                results.append(index)
    return sorted(results, key=lambda p: p.name if p.name != "index.md" else p.parent.name)


def scan_ids(worklog_root: Path | str, prefix: str) -> list[int]:
    """Scan active + archive dirs for items matching prefix (t/p/s).

    Matches both flat files ({prefix}NNNN-kebab.md) and directories
    ({prefix}NNNN-kebab/) by their entry name.
    Returns sorted list of numeric IDs found.
    """
    worklog_root = Path(worklog_root)
    prefix = prefix.lower()

    class_map = {"t": "task", "p": "plan", "s": "spec"}
    if prefix not in class_map:
        raise ValueError(f"Unknown prefix '{prefix}', expected one of: t, p, s")

    class_dir = class_map[prefix]
    ids: set[int] = set()

    # Directories to scan: active + archive
    scan_dirs = [worklog_root / class_dir]
    if prefix in ("t", "p"):
        scan_dirs.append(worklog_root / "archive" / class_dir)

    for d in scan_dirs:
        if not d.is_dir():
            continue
        for entry in d.iterdir():
            m = _ID_RE.match(entry.name)
            if m and m.group(1) == prefix:
                ids.add(int(m.group(2)))

    return sorted(ids)


def collect_all_items(
    worklog_root: Path,
    include_archive: bool = False,
    classes: tuple[str, ...] = ("task", "plan", "spec"),
) -> list[dict]:
    """Parse all items across specified classes.

    Returns list of frontmatter dicts (from parse_item).
    Silently skips items that fail to parse.
    """
    items: list[dict] = []
    scan_dirs: list[tuple[str, Path]] = []
    for cls in classes:
        prefix = CLASS_PREFIX[cls]
        scan_dirs.append((prefix, worklog_root / cls))
        if include_archive and cls in ("task", "plan"):
            scan_dirs.append((prefix, worklog_root / "archive" / cls))
    for prefix, class_dir in scan_dirs:
        for f in iter_items(class_dir, prefix):
            try:
                items.append(parse_item(f))
            except Exception:
                pass
    return items


def _serialize_toml_value(value: object) -> str:
    """Serialize a Python value to a TOML literal."""
    if value is None:
        raise ValueError("Cannot serialize None — use update_field with None to remove")
    if isinstance(value, list):
        items = ", ".join(f'"{v}"' for v in value)
        return f"[{items}]"
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    # Default: quoted string
    escaped = str(value).replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def update_field(path: Path, field: str, value: object) -> None:
    """Update a single TOML field in a +++‐delimited frontmatter block.

    If value is None, the field is removed.
    If the field exists, its line is replaced.
    If the field does not exist and value is not None, it is appended.
    """
    text = path.read_text(encoding="utf-8")
    if not text.startswith("+++\n"):
        raise ValueError(f"No frontmatter block in {path}")
    end = text.index("\n+++\n", 4)
    toml_block = text[4 : end + 1]  # includes trailing newline
    after = text[end + 5:]  # after closing +++\n

    field_re = re.compile(rf"^{re.escape(field)}\s*=.*$", re.MULTILINE)
    m = field_re.search(toml_block)

    if value is None:
        # Remove field
        if m:
            toml_block = toml_block[: m.start()] + toml_block[m.end() + 1 :]
    elif m:
        # Replace existing
        toml_block = toml_block[: m.start()] + f"{field} = {_serialize_toml_value(value)}" + toml_block[m.end() :]
    else:
        # Append new field
        toml_block += f"{field} = {_serialize_toml_value(value)}\n"

    path.write_text(f"+++\n{toml_block}+++\n{after}", encoding="utf-8")


def remove_from_list_field(path: Path, field: str, value_to_remove: str) -> bool:
    """Remove a value from a list field in frontmatter.

    Returns True if the field was modified, False if value was not present.
    Removes the field entirely if the list becomes empty.
    """
    item = parse_item(path)
    current = item.get(field, [])
    if not isinstance(current, list):
        return False
    lower_vals = [v.lower() for v in current]
    if value_to_remove.lower() not in lower_vals:
        return False
    new_list = [v for v in current if v.lower() != value_to_remove.lower()]
    update_field(path, field, new_list if new_list else None)
    return True
