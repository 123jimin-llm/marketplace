"""Playground composition → invoke-llm TOML mapping (pure logic, no LLM calls)."""

import itertools
import tomllib
from pathlib import Path

from util import split_frontmatter


def load_playground(pg_dir: Path) -> dict:
    """Load playground config, slot defaults, and input files.

    Returns {generation, composition, slots: {name: {default, dir}}, inputs: [Path, ...], pg_dir}.
    """
    pg_dir = Path(pg_dir).resolve()
    config_path = pg_dir / "config.toml"

    with open(config_path, "rb") as f:
        config = tomllib.load(f)

    generation = config.get("generation", {})
    composition = config.get("composition", {})

    # Scan slot directories under prompts/
    slots = {}
    prompts_dir = pg_dir / "prompts"
    if prompts_dir.is_dir():
        for slot_dir in sorted(prompts_dir.iterdir()):
            if not slot_dir.is_dir():
                continue
            slot_config_path = slot_dir / "config.toml"
            default = "base"
            if slot_config_path.exists():
                with open(slot_config_path, "rb") as f:
                    slot_cfg = tomllib.load(f)
                default = slot_cfg.get("default", "base")
            slots[slot_dir.name] = {"default": default, "dir": slot_dir}

    # Glob input files
    inputs_dir = pg_dir / "inputs"
    inputs = sorted(inputs_dir.glob("*.md")) if inputs_dir.is_dir() else []

    return {
        "generation": generation,
        "composition": composition,
        "slots": slots,
        "inputs": inputs,
        "pg_dir": pg_dir,
    }


def expand_variations(pg_config: dict, variation_spec: dict[str, list[str]]) -> list[dict[str, str]]:
    """Expand variation spec into cartesian product of concrete slot choices.

    variation_spec: {slot: [var1, var2, ...]}. ["*"] expands to all .md files in slot dir.
    Omitted slots use their default variation.
    Returns list of {slot: variation_name} dicts.
    """
    slots = pg_config["slots"]

    # Build full spec with defaults for omitted slots
    full_spec = {}
    for slot_name, slot_info in slots.items():
        if slot_name in variation_spec:
            variants = variation_spec[slot_name]
        else:
            variants = [slot_info["default"]]

        # Expand "*" glob
        expanded = []
        for v in variants:
            if v == "*":
                slot_dir = slot_info["dir"]
                md_files = sorted(slot_dir.glob("*.md"))
                expanded.extend(f.stem for f in md_files)
            else:
                expanded.append(v)
        full_spec[slot_name] = expanded

    # Cartesian product
    slot_names = list(full_spec.keys())
    if not slot_names:
        return [{}]

    value_lists = [full_spec[name] for name in slot_names]
    combos = []
    for combo in itertools.product(*value_lists):
        combos.append(dict(zip(slot_names, combo)))
    return combos


def _resolve_part(part: str, pg_config: dict, variation_combo: dict[str, str],
                  input_file: Path) -> tuple[str, Path | None]:
    """Resolve a single composition part to (text_content, file_path_relative_to_pg_dir).

    Returns the resolved text (frontmatter stripped) and the relative path for TOML output.
    """
    pg_dir = pg_config["pg_dir"]
    slots = pg_config["slots"]

    if part == "inputs":
        text = input_file.read_text(encoding="utf-8")
        _, _, body = split_frontmatter(text)
        rel_path = input_file.relative_to(pg_dir)
        return body, rel_path

    part_path = Path(part)
    # Check if it's a slot directory (e.g., "prompts/main")
    if len(part_path.parts) >= 2 and part_path.parts[0] == "prompts":
        slot_name = part_path.parts[1]
        if slot_name in slots:
            variation = variation_combo.get(slot_name, slots[slot_name]["default"])
            resolved = pg_dir / "prompts" / slot_name / f"{variation}.md"
            try:
                text = resolved.read_text(encoding="utf-8")
            except FileNotFoundError:
                raise FileNotFoundError(
                    f"Slot '{slot_name}' variation '{variation}' not found: {resolved}"
                )
            _, _, body = split_frontmatter(text)
            rel_path = resolved.relative_to(pg_dir)
            return body, rel_path

    # Direct file path
    resolved = pg_dir / part
    try:
        text = resolved.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise FileNotFoundError(f"Prompt file not found: {resolved}")
    _, _, body = split_frontmatter(text)
    rel_path = Path(part)
    return body, rel_path


def build_run_spec(pg_config: dict, variation_combo: dict[str, str], input_file: Path) -> dict:
    """Map composition → invoke-llm spec for one (combo, input) pair.

    Returns {toml_dict, user_message, system, model, temperature, max_tokens}.
    toml_dict is serializable to a valid standalone invoke-llm TOML.
    """
    gen = pg_config["generation"]
    comp = pg_config["composition"]
    pg_dir = pg_config["pg_dir"]

    model = gen.get("model", "claude-sonnet-4-6")
    temperature = gen.get("temperature", 1.0)
    max_tokens = gen.get("max_tokens", 4096)
    root_separator = comp.get("separator", "\n\n")
    root_substitute = comp.get("substitute", False)

    # Build the TOML dict
    toml_gen = {"model": model, "temperature": temperature, "max_tokens": max_tokens}
    if root_separator != "\n\n":
        toml_gen["separator"] = root_separator
    toml_prompts = []
    toml_vars = {}

    # Output dir is outputs/<label>/ — run.toml lives there.
    # Paths in TOML are relative to run.toml's parent, so we need ../../ prefix.
    rel_prefix = "../../"

    if "messages" in comp:
        # Multi-message mode
        messages = comp["messages"]
        resolved_messages = []

        for msg in messages:
            role = msg["role"]
            parts = msg.get("parts", [])
            msg_separator = msg.get("separator", root_separator)
            msg_substitute = msg.get("substitute", root_substitute)

            msg_texts = []
            for part in parts:
                if part == "inputs" and msg_substitute:
                    # substitute mode: input goes into vars
                    _, input_rel = _resolve_part("inputs", pg_config, variation_combo, input_file)
                    toml_vars["input"] = rel_prefix + str(input_rel).replace("\\", "/")
                    continue

                text, rel_path = _resolve_part(part, pg_config, variation_combo, input_file)
                msg_texts.append(text)

                entry = {"role": role, "file": rel_prefix + str(rel_path).replace("\\", "/")}
                if msg_substitute:
                    entry["substitute"] = True
                toml_prompts.append(entry)

                if part == "inputs" and not msg_substitute:
                    pass  # already handled above

            resolved_messages.append({
                "role": role,
                "texts": msg_texts,
                "separator": msg_separator,
                "substitute": msg_substitute,
            })
    else:
        # Single-message mode
        parts = comp.get("parts", [])
        role = comp.get("role", "user")
        substitute = root_substitute

        for part in parts:
            if part == "inputs" and substitute:
                # substitute mode: input goes into vars, skip adding as prompt entry
                _, input_rel = _resolve_part("inputs", pg_config, variation_combo, input_file)
                toml_vars["input"] = rel_prefix + str(input_rel).replace("\\", "/")
                continue

            text, rel_path = _resolve_part(part, pg_config, variation_combo, input_file)
            entry = {"role": role, "file": rel_prefix + str(rel_path).replace("\\", "/")}
            if substitute:
                entry["substitute"] = True
            toml_prompts.append(entry)

    # Assemble toml_dict
    toml_dict = {"generation": toml_gen}
    if toml_vars:
        toml_dict["vars"] = toml_vars
    toml_dict["prompts"] = toml_prompts

    # Also compute resolved texts for direct invoke_llm() calls
    system_text, user_text = _resolve_messages(pg_config, comp, variation_combo, input_file)

    return {
        "toml_dict": toml_dict,
        "user_message": user_text,
        "system": system_text,
        "model": model,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }


def _resolve_messages(pg_config: dict, comp: dict, variation_combo: dict[str, str],
                      input_file: Path) -> tuple[str | None, str]:
    """Resolve composition into (system_text, user_text) for direct LLM invocation."""
    root_separator = comp.get("separator", "\n\n")
    root_substitute = comp.get("substitute", False)

    if "messages" in comp:
        system_parts = []
        user_parts = []

        for msg in comp["messages"]:
            role = msg["role"]
            parts = msg.get("parts", [])
            msg_separator = msg.get("separator", root_separator)
            msg_substitute = msg.get("substitute", root_substitute)

            texts = []
            input_text = None
            for part in parts:
                text, _ = _resolve_part(part, pg_config, variation_combo, input_file)
                if part == "inputs" and msg_substitute:
                    input_text = text
                    continue
                if msg_substitute and input_text is not None:
                    text = text.replace("{{input}}", input_text)
                texts.append(text)

            # If substitute and input was seen, apply to all texts
            if msg_substitute and input_text is not None:
                texts = [t.replace("{{input}}", input_text) for t in texts]

            joined = msg_separator.join(texts)

            if role == "system":
                system_parts.append(joined)
            else:
                user_parts.append(joined)

        system = root_separator.join(system_parts) if system_parts else None
        user = root_separator.join(user_parts)
        return system, user
    else:
        # Single-message mode
        parts = comp.get("parts", [])
        role = comp.get("role", "user")
        substitute = root_substitute

        texts = []
        input_text = None
        for part in parts:
            text, _ = _resolve_part(part, pg_config, variation_combo, input_file)
            if part == "inputs" and substitute:
                input_text = text
                continue
            texts.append(text)

        if substitute and input_text is not None:
            texts = [t.replace("{{input}}", input_text) for t in texts]

        joined = root_separator.join(texts)

        if role == "system":
            return joined, ""
        else:
            return None, joined


def serialize_toml(config_dict: dict) -> str:
    """Hand-written TOML serializer — no tomli_w dependency.

    Handles [generation], [vars], and [[prompts]] sections.
    """
    lines = []

    # [generation]
    gen = config_dict.get("generation", {})
    if gen:
        lines.append("[generation]")
        for key, value in gen.items():
            lines.append(f"{key} = {_toml_value(value)}")
        lines.append("")

    # [vars]
    vars_section = config_dict.get("vars", {})
    if vars_section:
        lines.append("[vars]")
        for key, value in vars_section.items():
            lines.append(f"{key} = {_toml_value(value)}")
        lines.append("")

    # [[prompts]]
    prompts = config_dict.get("prompts", [])
    for entry in prompts:
        lines.append("[[prompts]]")
        # role first, then file/prompt, then other keys
        if "role" in entry:
            lines.append(f"role = {_toml_value(entry['role'])}")
        if "file" in entry:
            lines.append(f"file = {_toml_value(entry['file'])}")
        if "prompt" in entry:
            lines.append(f"prompt = {_toml_value(entry['prompt'])}")
        for key, value in entry.items():
            if key in ("role", "file", "prompt"):
                continue
            lines.append(f"{key} = {_toml_value(value)}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def _toml_value(value) -> str:
    """Format a Python value as a TOML value string."""
    if isinstance(value, bool):
        return "true" if value else "false"
    elif isinstance(value, int):
        return str(value)
    elif isinstance(value, float):
        # Use repr to preserve precision, but ensure it's valid TOML
        s = repr(value)
        if s == "inf":
            return "inf"
        return s
    elif isinstance(value, str):
        return _toml_string(value)
    elif isinstance(value, list):
        items = ", ".join(_toml_value(v) for v in value)
        return f"[{items}]"
    else:
        return repr(value)


def _toml_string(s: str) -> str:
    """Format a string as a TOML quoted string."""
    # Use basic string with escapes
    escaped = s.replace("\\", "\\\\").replace('"', '\\"')
    escaped = escaped.replace("\n", "\\n").replace("\t", "\\t").replace("\r", "\\r")
    return f'"{escaped}"'
