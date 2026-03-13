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

    # Generation sweep dimensions
    models = _ensure_list(gen.get("model", "claude-sonnet-4-6"))
    temperatures = _ensure_list(gen.get("temperature", 1.0))
    max_tokens_list = _ensure_list(gen.get("max_tokens", 4096))

    # Group prompt entries by role, preserving order within each role
    # Each entry becomes a sweep dimension (array values) or fixed (scalar)
    system_entries = []  # list of list[(label, text)]
    user_entries = []

    for entry in prompts:
        role = entry.get("role")
        if role not in ("system", "user"):
            raise ValueError(f"Unknown prompt role: {role!r} (must be 'system' or 'user')")
        resolved = _resolve_prompt_entry(entry, base_dir)
        if role == "system":
            system_entries.append(resolved)
        else:
            user_entries.append(resolved)

    if not user_entries:
        raise ValueError("Config has no user prompts in [[prompts]]")

    # Build sweep dimensions for prompt entries
    # Each entry's resolved list is a sweep dimension; we take the cartesian product
    # Then within each combination, same-role entries are concatenated
    system_combos = list(itertools.product(*system_entries)) if system_entries else [()]
    user_combos = list(itertools.product(*user_entries)) if user_entries else [()]

    runs = []
    for model in models:
        for temp in temperatures:
            for max_tok in max_tokens_list:
                for sys_combo in system_combos:
                    for usr_combo in user_combos:
                        # Concatenate same-role entries
                        sys_text = "\n\n".join(text for _, text in sys_combo) if sys_combo else None
                        usr_text = "\n\n".join(text for _, text in usr_combo)

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
