"""Shared utilities for prompt-engineer scripts."""

import re
import time


def split_frontmatter(text: str) -> tuple[str, str, str]:
    """Split frontmatter from body. Supports TOML (+++) and YAML (---) delimiters.

    Returns (description, frontmatter, body).
    """
    for delim in ("+++", "---"):
        m = re.match(rf"^{re.escape(delim)}\n(.*?\n){re.escape(delim)}\n?", text, re.DOTALL)
        if m:
            fm = m.group(1)
            desc = ""
            dm = re.search(r"^description\s*[=:]\s*(.+)$", fm, re.MULTILINE)
            if dm:
                desc = dm.group(1).strip().strip('"\'')
            return desc, fm, text[m.end():]
    return "", "", text


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


def invoke_llm(
    user_message: str,
    *,
    system: str | None = None,
    model: str = "claude-sonnet-4-6",
    temperature: float = 1.0,
    max_tokens: int = 4096,
) -> dict:
    """Invoke an LLM and return response with metadata.

    Routes to Anthropic or OpenAI based on model name.
    Returns { response, model, input_tokens, output_tokens, latency_ms, stop_reason }.
    """
    start = time.perf_counter()

    if is_claude(model):
        from anthropic import Anthropic

        kwargs = dict(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[{"role": "user", "content": user_message}],
        )
        if system:
            kwargs["system"] = system

        resp = Anthropic().messages.create(**kwargs)
        elapsed = (time.perf_counter() - start) * 1000

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

        resp = OpenAI().chat.completions.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=messages,
        )
        elapsed = (time.perf_counter() - start) * 1000
        choice = resp.choices[0]

        return {
            "response": choice.message.content,
            "model": resp.model,
            "input_tokens": resp.usage.prompt_tokens,
            "output_tokens": resp.usage.completion_tokens,
            "latency_ms": round(elapsed),
            "stop_reason": choice.finish_reason,
        }
