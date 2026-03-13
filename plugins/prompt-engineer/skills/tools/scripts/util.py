"""Shared utilities for prompt-engineer scripts."""

import re


def split_frontmatter(text: str) -> tuple[str, str, str]:
    """Split YAML frontmatter from body. Returns (description, frontmatter, body)."""
    m = re.match(r"^---\n(.*?\n)---\n?", text, re.DOTALL)
    if not m:
        return "", "", text
    fm = m.group(1)
    desc = ""
    dm = re.search(r"^description:\s*(.+)$", fm, re.MULTILINE)
    if dm:
        desc = dm.group(1).strip()
    return desc, fm, text[m.end():]


def split_sections(text: str) -> list[tuple[str, str]]:
    """Split markdown on ## headers. Returns [(header, body), ...]."""
    parts = re.split(r"^(##\s+.+)$", text, flags=re.MULTILINE)
    sections = []
    if parts[0].strip():
        sections.append(("(heading)", parts[0]))
    for i in range(1, len(parts), 2):
        header = parts[i].strip()
        body = parts[i + 1] if i + 1 < len(parts) else ""
        sections.append((header, body))
    return sections


def is_claude(model: str) -> bool:
    return model.startswith("claude")


def count_tokens(text: str, model: str) -> int:
    if is_claude(model):
        from anthropic import Anthropic
        resp = Anthropic().messages.count_tokens(
            model=model,
            messages=[{"role": "user", "content": text}],
        )
        return resp.input_tokens
    else:
        import tiktoken
        try:
            enc = tiktoken.encoding_for_model(model)
        except KeyError:
            enc = tiktoken.get_encoding(model)
        return len(enc.encode(text))
