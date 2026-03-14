"""Shared utilities for prompt-engineer scripts."""

import re
import time
import tomllib
from typing import NamedTuple


class ParsedDoc(NamedTuple):
    frontmatter: dict
    body: str


def _parse_yaml_flat(text: str) -> dict:
    """Parse flat YAML (key: value pairs only, as used in frontmatter)."""
    result = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        key, sep, value = line.partition(":")
        if not sep:
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
            value = value[1:-1]
        result[key.strip()] = value
    return result


def split_frontmatter(text: str) -> ParsedDoc:
    """Split frontmatter from body. Supports TOML (+++) and YAML (---) delimiters.

    Returns ParsedDoc(frontmatter, body) where frontmatter is a parsed dict.
    Raises ValueError if an unclosed frontmatter block is detected.
    """
    for delim, pattern, parser in (
        ("+++", r"^\+\+\+\n(.*?\n)\+\+\+\n?", tomllib.loads),
        ("---", r"^---\n(.*?\n)---\n?", _parse_yaml_flat),
    ):
        if text.startswith(delim + "\n"):
            m = re.match(pattern, text, re.DOTALL)
            if not m:
                raise ValueError(f"Unclosed frontmatter block (expected closing '{delim}')")
            return ParsedDoc(parser(m.group(1)), text[m.end():])
    return ParsedDoc({}, text)


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


def read_input(value: str, is_file: bool = False) -> str:
    """Resolve a string-or-file input to its text content."""
    if is_file:
        with open(value, encoding="utf-8") as f:
            return f.read()
    return value


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


def toml_str(s: str, *, multiline: bool = False) -> str:
    """Serialize a string as a TOML value.

    When multiline=True, strings containing newlines use triple-quoted literals.
    Otherwise, newlines are escaped (safe default for config fields).
    """
    if multiline and "\n" in s:
        escaped = s.replace("\\", "\\\\")
        # Break any run of 3+ quotes so it can't collide with the delimiter.
        escaped = re.sub(r'"{3,}', lambda m: '"\\"' * (len(m.group()) // 2) + '"' * (len(m.group()) % 2), escaped)
        # A trailing " or "" before the closing """ would form """" or """"".
        if escaped.endswith('"'):
            escaped = escaped[:-1] + '\\"'
        return f'"""\n{escaped}"""'
    escaped = s.replace("\\", "\\\\").replace('"', '\\"')
    escaped = escaped.replace("\n", "\\n").replace("\t", "\\t").replace("\r", "\\r")
    return f'"{escaped}"'


def invoke_llm(
    user_message: str,
    *,
    system: str | None = None,
    model: str = "claude-sonnet-4-6",
    temperature: float = 1.0,
    max_tokens: int | None = None,
) -> dict:
    """Invoke an LLM and return response with metadata.

    Routes to Anthropic or OpenAI based on model name.
    max_tokens is required for Claude (defaults to 4096); optional for OpenAI (omitted if None).
    Returns { response, model, input_tokens, output_tokens, latency_ms, stop_reason }.
    """
    start = time.perf_counter()

    if is_claude(model):
        from anthropic import Anthropic

        kwargs = dict(
            model=model,
            max_tokens=max_tokens or 4096,
            temperature=temperature,
            messages=[{"role": "user", "content": user_message}],
        )
        if system:
            kwargs["system"] = system

        resp = Anthropic().messages.create(**kwargs)
        elapsed = (time.perf_counter() - start) * 1000

        if not resp.content or not hasattr(resp.content[0], "text"):
            raise ValueError(f"Unexpected response content: {resp.content!r}")
        return {
            "response": resp.content[0].text,
            "model": resp.model,
            "input_tokens": resp.usage.input_tokens,
            "output_tokens": resp.usage.output_tokens,
            "latency_ms": round(elapsed),
            "stop_reason": resp.stop_reason,
        }
    else:
        from openai import OpenAI

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": user_message})

        kwargs = dict(
            model=model,
            temperature=temperature,
            messages=messages,
        )
        if max_tokens is not None:
            kwargs["max_completion_tokens"] = max_tokens

        resp = OpenAI().chat.completions.create(**kwargs)
        elapsed = (time.perf_counter() - start) * 1000

        if not resp.choices:
            raise ValueError("No choices in OpenAI response")
        choice = resp.choices[0]
        if choice.message.content is None:
            raise ValueError("No content in OpenAI response message")
        return {
            "response": choice.message.content,
            "model": resp.model,
            "input_tokens": resp.usage.prompt_tokens,
            "output_tokens": resp.usage.completion_tokens,
            "latency_ms": round(elapsed),
            "stop_reason": choice.finish_reason,
        }
