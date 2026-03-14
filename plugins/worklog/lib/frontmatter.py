"""Shared TOML frontmatter parsing and ID scanning for worklog scripts."""

import re
import tomllib
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
_CLASS_PREFIX = {"task": "t", "plan": "p", "spec": "s"}


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


def promote_to_dir(flat_file: Path) -> Path:
    """Promote a flat item file to directory format.

    task/t0001-foo.md → task/t0001-foo/index.md
    Returns the new path.
    """
    if not flat_file.is_file() or flat_file.suffix != ".md":
        raise ValueError(f"Expected a .md file, got: {flat_file}")
    dir_path = flat_file.parent / flat_file.stem
    dir_path.mkdir(exist_ok=True)
    new_path = dir_path / "index.md"
    flat_file.rename(new_path)
    return new_path


def scan_ids(worklog_root: Path | str, prefix: str) -> list[int]:
    """Scan active + archive dirs for items matching prefix (t/p/s).

    For tasks and plans (t/p), scans subfolder names.
    For specs (s), scans filenames directly.
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
