"""TOML config loading and matrix expansion for invoke-llm."""

import itertools
import tomllib
from pathlib import Path


def load_config(path: str) -> dict:
    """Parse a TOML config file and return the raw config dict.

    Resolves file paths in [[prompts]] entries relative to the TOML file's parent directory.
    """
    config_path = Path(path).resolve()
    base_dir = config_path.parent

    with open(config_path, "rb") as f:
        config = tomllib.load(f)

    config["_base_dir"] = base_dir
    return config


def resolve_value(value: str, base_dir: Path) -> str:
    """Read file content, resolved relative to base_dir."""
    resolved = base_dir / value
    try:
        return resolved.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise FileNotFoundError(f"File not found: {resolved}")


def _ensure_list(value):
    """Wrap scalars in a list; pass lists through."""
    if isinstance(value, list):
        return value
    return [value]


def _resolve_prompt_entry(entry: dict, base_dir: Path) -> list[tuple[str, str]]:
    """Resolve a single [[prompts]] entry to a list of (label, text) pairs.

    Each pair represents one sweep value. For scalar file/prompt, returns one pair.
    For array file/prompt, returns one pair per element.
    """
    role = entry["role"]
    if "file" in entry and "prompt" in entry:
        raise ValueError(f"Prompt entry has both 'file' and 'prompt': {entry}")
    if "file" not in entry and "prompt" not in entry:
        raise ValueError(f"Prompt entry missing 'file' or 'prompt': {entry}")

    if "file" in entry:
        files = _ensure_list(entry["file"])
        return [(f, resolve_value(f, base_dir)) for f in files]
    else:
        prompts = _ensure_list(entry["prompt"])
        labels = []
        for p in prompts:
            label = p if len(p) <= 30 else p[:27] + "..."
            labels.append(label)
        return list(zip(labels, prompts))


def _resolve_vars(config: dict) -> dict[str, str]:
    """Resolve [vars] section: read each value as a file path relative to _base_dir."""
    base_dir = config["_base_dir"]
    raw_vars = config.get("vars", {})
    resolved = {}
    for name, path in raw_vars.items():
        resolved[name] = resolve_value(path, base_dir)
    return resolved


def _apply_substitute(text: str, resolved_vars: dict[str, str]) -> str:
    """Replace {{key}} placeholders in text with resolved var values."""
    for key, value in resolved_vars.items():
        text = text.replace("{{" + key + "}}", value)
    return text


def expand_matrix(config: dict) -> list[dict]:
    """Build cartesian product of sweep dimensions from a parsed config.

    Returns a list of RunSpec dicts, each with:
        user_message, system, model, temperature, max_tokens, labels
    """
    base_dir = config["_base_dir"]
    gen = config.get("generation", {})
    prompts = config.get("prompts", None)

    if prompts is None:
        raise ValueError("Config missing [[prompts]] section (required for invoke-llm)")

    # Resolve [vars] section
    resolved_vars = _resolve_vars(config)

    # Top-level separator
    top_separator = gen.get("separator", "\n\n")

    # Generation sweep dimensions
    models = _ensure_list(gen.get("model", "claude-sonnet-4-6"))
    temperatures = _ensure_list(gen.get("temperature", 1.0))
    max_tokens_list = _ensure_list(gen.get("max_tokens", 4096))

    # Group prompt entries by role, preserving order within each role
    system_entries = []  # list of list[(label, text)]
    user_entries = []
    system_meta = []  # per-entry: (separator, substitute)
    user_meta = []

    for entry in prompts:
        role = entry.get("role")
        if role not in ("system", "user"):
            raise ValueError(f"Unknown prompt role: {role!r} (must be 'system' or 'user')")

        resolved = _resolve_prompt_entry(entry, base_dir)
        meta = (entry.get("separator", None), entry.get("substitute", False))

        if role == "system":
            system_entries.append(resolved)
            system_meta.append(meta)
        else:
            user_entries.append(resolved)
            user_meta.append(meta)

    if not user_entries:
        raise ValueError("Config has no user prompts in [[prompts]]")

    # Build sweep dimensions
    system_combos = list(itertools.product(*system_entries)) if system_entries else [()]
    user_combos = list(itertools.product(*user_entries)) if user_entries else [()]

    runs = []
    for model in models:
        for temp in temperatures:
            for max_tok in max_tokens_list:
                for sys_combo in system_combos:
                    for usr_combo in user_combos:
                        sys_text = _join_parts(sys_combo, system_meta, top_separator, resolved_vars) if sys_combo else None
                        usr_text = _join_parts(usr_combo, user_meta, top_separator, resolved_vars)

                        # Build labels
                        sys_label = "/".join(label for label, _ in sys_combo) if sys_combo else None
                        usr_label = "+".join(label for label, _ in usr_combo)

                        labels = {
                            "model": model,
                            "temperature": temp,
                            "user": usr_label,
                        }
                        if sys_label:
                            labels["system"] = sys_label

                        runs.append({
                            "user_message": usr_text,
                            "system": sys_text,
                            "model": model,
                            "temperature": temp,
                            "max_tokens": max_tok,
                            "labels": labels,
                        })

    return runs


def _join_parts(
    combo: tuple,
    meta: list[tuple],
    top_separator: str,
    resolved_vars: dict[str, str],
) -> str:
    """Join a combo of (label, text) pairs using per-entry separators and substitution."""
    parts = []
    for i, (_, text) in enumerate(combo):
        _, do_substitute = meta[i]
        if do_substitute and resolved_vars:
            text = _apply_substitute(text, resolved_vars)
        parts.append(text)

    if not parts:
        return ""

    result = parts[0]
    for i in range(1, len(parts)):
        entry_sep, _ = meta[i]
        sep = entry_sep if entry_sep is not None else top_separator
        result += sep + parts[i]
    return result


def matrix_dimensions(config: dict) -> dict:
    """Return a summary of sweep dimensions and total run count."""
    base_dir = config["_base_dir"]
    gen = config.get("generation", {})
    prompts = config.get("prompts", [])

    dims = {}

    models = _ensure_list(gen.get("model", "claude-sonnet-4-6"))
    if len(models) > 1:
        dims["model"] = models

    temps = _ensure_list(gen.get("temperature", 1.0))
    if len(temps) > 1:
        dims["temperature"] = temps

    max_toks = _ensure_list(gen.get("max_tokens", 4096))
    if len(max_toks) > 1:
        dims["max_tokens"] = max_toks

    for entry in prompts:
        role = entry.get("role", "?")
        key = "file" if "file" in entry else "prompt"
        values = _ensure_list(entry.get(key, []))
        if len(values) > 1:
            dim_name = f"{role}.{key}"
            dims[dim_name] = values

    total = 1
    for v in dims.values():
        total *= len(v)
    # Also multiply by fixed dimensions (count=1 each)
    # Actually need total from expand_matrix logic
    total = len(models) * len(temps) * len(max_toks)
    for entry in prompts:
        key = "file" if "file" in entry else "prompt"
        values = _ensure_list(entry.get(key, []))
        total *= len(values)

    return {"dimensions": dims, "total_runs": total}
