"""Tests for lib/playground.py — playground loading, variation expansion, and run spec building."""

import sys
import textwrap
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))

from playground import (
    load_playground,
    expand_variations,
    build_run_spec,
    serialize_toml,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _scaffold(tmp_path, config_toml, slots=None, inputs=None, extra_files=None):
    """Create a minimal playground structure under tmp_path."""
    (tmp_path / "config.toml").write_text(config_toml, encoding="utf-8")

    # Slots: {name: {default: str, variations: {var_name: content}}}
    for slot_name, slot_info in (slots or {}).items():
        slot_dir = tmp_path / "prompts" / slot_name
        slot_dir.mkdir(parents=True, exist_ok=True)
        default = slot_info.get("default", "base")
        (slot_dir / "config.toml").write_text(
            f'default = "{default}"\n', encoding="utf-8"
        )
        for var_name, content in slot_info.get("variations", {}).items():
            (slot_dir / f"{var_name}.md").write_text(content, encoding="utf-8")

    # Inputs: {case_name: content}
    if inputs:
        inputs_dir = tmp_path / "inputs"
        inputs_dir.mkdir(exist_ok=True)
        for name, content in inputs.items():
            (inputs_dir / f"{name}.md").write_text(content, encoding="utf-8")

    # Extra files: {relative_path: content}
    for rel_path, content in (extra_files or {}).items():
        fp = tmp_path / rel_path
        fp.parent.mkdir(parents=True, exist_ok=True)
        fp.write_text(content, encoding="utf-8")


# ---------------------------------------------------------------------------
# load_playground
# ---------------------------------------------------------------------------

class TestLoadPlayground:
    def test_basic_load(self, tmp_path):
        _scaffold(tmp_path,
            config_toml=textwrap.dedent("""\
                [generation]
                model = "claude-sonnet-4-6"

                [composition]
                parts = ["prompts/main", "inputs"]
            """),
            slots={"main": {"default": "base", "variations": {"base": "Do the thing."}}},
            inputs={"case1": "Input one."},
        )
        pg = load_playground(tmp_path)
        assert pg["generation"]["model"] == "claude-sonnet-4-6"
        assert "main" in pg["slots"]
        assert pg["slots"]["main"]["default"] == "base"
        assert len(pg["inputs"]) == 1
        assert pg["inputs"][0].name == "case1.md"

    def test_multiple_slots_and_inputs(self, tmp_path):
        _scaffold(tmp_path,
            config_toml="[generation]\n[composition]\nparts = []\n",
            slots={
                "main": {"default": "base", "variations": {"base": "A", "concise": "B"}},
                "system": {"default": "strict", "variations": {"strict": "S"}},
            },
            inputs={"case1": "One", "case2": "Two"},
        )
        pg = load_playground(tmp_path)
        assert set(pg["slots"].keys()) == {"main", "system"}
        assert len(pg["inputs"]) == 2

    def test_missing_slot_config_defaults_to_base(self, tmp_path):
        _scaffold(tmp_path,
            config_toml="[generation]\n[composition]\nparts = []\n",
            slots={"main": {"default": "base", "variations": {"base": "X"}}},
        )
        # Remove the slot config.toml to test fallback
        (tmp_path / "prompts" / "main" / "config.toml").unlink()
        pg = load_playground(tmp_path)
        assert pg["slots"]["main"]["default"] == "base"


# ---------------------------------------------------------------------------
# expand_variations
# ---------------------------------------------------------------------------

class TestExpandVariations:
    def test_default_only(self, tmp_path):
        _scaffold(tmp_path,
            config_toml="[generation]\n[composition]\nparts = []\n",
            slots={"main": {"default": "base", "variations": {"base": "X"}}},
        )
        pg = load_playground(tmp_path)
        combos = expand_variations(pg, {})
        assert combos == [{"main": "base"}]

    def test_explicit_single(self, tmp_path):
        _scaffold(tmp_path,
            config_toml="[generation]\n[composition]\nparts = []\n",
            slots={"main": {"default": "base", "variations": {"base": "X", "concise": "Y"}}},
        )
        pg = load_playground(tmp_path)
        combos = expand_variations(pg, {"main": ["concise"]})
        assert combos == [{"main": "concise"}]

    def test_multiple_variations_sweep(self, tmp_path):
        _scaffold(tmp_path,
            config_toml="[generation]\n[composition]\nparts = []\n",
            slots={"main": {"default": "base", "variations": {"base": "X", "concise": "Y"}}},
        )
        pg = load_playground(tmp_path)
        combos = expand_variations(pg, {"main": ["base", "concise"]})
        assert len(combos) == 2
        assert {"main": "base"} in combos
        assert {"main": "concise"} in combos

    def test_star_glob_expansion(self, tmp_path):
        _scaffold(tmp_path,
            config_toml="[generation]\n[composition]\nparts = []\n",
            slots={"main": {"default": "base", "variations": {"base": "X", "concise": "Y", "verbose": "Z"}}},
        )
        pg = load_playground(tmp_path)
        combos = expand_variations(pg, {"main": ["*"]})
        assert len(combos) == 3
        names = {c["main"] for c in combos}
        assert names == {"base", "concise", "verbose"}

    def test_cartesian_product_multi_slot(self, tmp_path):
        _scaffold(tmp_path,
            config_toml="[generation]\n[composition]\nparts = []\n",
            slots={
                "main": {"default": "base", "variations": {"base": "X", "concise": "Y"}},
                "system": {"default": "strict", "variations": {"strict": "S", "relaxed": "R"}},
            },
        )
        pg = load_playground(tmp_path)
        combos = expand_variations(pg, {"main": ["base", "concise"], "system": ["strict", "relaxed"]})
        # 2 × 2 = 4
        assert len(combos) == 4

    def test_omitted_slot_uses_default(self, tmp_path):
        _scaffold(tmp_path,
            config_toml="[generation]\n[composition]\nparts = []\n",
            slots={
                "main": {"default": "base", "variations": {"base": "X", "concise": "Y"}},
                "system": {"default": "strict", "variations": {"strict": "S"}},
            },
        )
        pg = load_playground(tmp_path)
        combos = expand_variations(pg, {"main": ["base", "concise"]})
        # main sweeps 2, system defaults to strict → 2 combos
        assert len(combos) == 2
        assert all(c["system"] == "strict" for c in combos)


# ---------------------------------------------------------------------------
# build_run_spec — single-message mode
# ---------------------------------------------------------------------------

class TestBuildRunSpecSingleMessage:
    def test_basic_parts(self, tmp_path):
        _scaffold(tmp_path,
            config_toml=textwrap.dedent("""\
                [generation]
                model = "test-model"
                temperature = 0.5
                max_tokens = 1000

                [composition]
                parts = ["prompts/main", "inputs"]
            """),
            slots={"main": {"default": "base", "variations": {"base": "Do the thing."}}},
            inputs={"case1": "Input one."},
        )
        pg = load_playground(tmp_path)
        spec = build_run_spec(pg, {"main": "base"}, pg["inputs"][0])

        assert spec["model"] == "test-model"
        assert spec["temperature"] == 0.5
        assert spec["max_tokens"] == 1000
        assert "Do the thing." in spec["user_message"]
        assert "Input one." in spec["user_message"]
        assert spec["system"] is None

        # TOML dict should have prompts entries
        td = spec["toml_dict"]
        assert td["generation"]["model"] == "test-model"
        assert len(td["prompts"]) == 2

    def test_substitute_mode(self, tmp_path):
        _scaffold(tmp_path,
            config_toml=textwrap.dedent("""\
                [generation]
                model = "test-model"

                [composition]
                parts = ["prompts/main", "inputs"]
                substitute = true
            """),
            slots={"main": {"default": "base", "variations": {"base": "Process: {{input}}"}}},
            inputs={"case1": "My input data."},
        )
        pg = load_playground(tmp_path)
        spec = build_run_spec(pg, {"main": "base"}, pg["inputs"][0])

        # In substitute mode, input goes into vars, not as separate prompt
        td = spec["toml_dict"]
        assert "vars" in td
        assert "input" in td["vars"]
        # Only one prompt entry (the template), not two
        assert len(td["prompts"]) == 1
        assert td["prompts"][0].get("substitute") is True

        # Resolved user_message should have substitution applied
        assert "My input data." in spec["user_message"]

    def test_non_substitute_adds_input_as_prompt(self, tmp_path):
        _scaffold(tmp_path,
            config_toml=textwrap.dedent("""\
                [generation]
                model = "test-model"

                [composition]
                parts = ["prompts/main", "inputs"]
                substitute = false
            """),
            slots={"main": {"default": "base", "variations": {"base": "Analyze this:"}}},
            inputs={"case1": "Test input."},
        )
        pg = load_playground(tmp_path)
        spec = build_run_spec(pg, {"main": "base"}, pg["inputs"][0])

        td = spec["toml_dict"]
        assert "vars" not in td
        assert len(td["prompts"]) == 2

    def test_frontmatter_stripped(self, tmp_path):
        _scaffold(tmp_path,
            config_toml=textwrap.dedent("""\
                [generation]
                model = "test-model"

                [composition]
                parts = ["prompts/main", "inputs"]
            """),
            slots={"main": {"default": "base", "variations": {
                "base": "---\ncomments: This is a note.\n---\nActual prompt text."
            }}},
            inputs={"case1": "---\ncomments: Input note.\n---\nInput body."},
        )
        pg = load_playground(tmp_path)
        spec = build_run_spec(pg, {"main": "base"}, pg["inputs"][0])

        assert "comments:" not in spec["user_message"]
        assert "Actual prompt text." in spec["user_message"]
        assert "Input body." in spec["user_message"]

    def test_custom_separator(self, tmp_path):
        _scaffold(tmp_path,
            config_toml=textwrap.dedent("""\
                [generation]
                model = "test-model"

                [composition]
                parts = ["prompts/main", "inputs"]
                separator = "\\n---\\n"
            """),
            slots={"main": {"default": "base", "variations": {"base": "Prompt."}}},
            inputs={"case1": "Input."},
        )
        pg = load_playground(tmp_path)
        spec = build_run_spec(pg, {"main": "base"}, pg["inputs"][0])

        td = spec["toml_dict"]
        assert td["generation"].get("separator") == "\n---\n"

    def test_path_relativity(self, tmp_path):
        """run.toml paths should use ../../ prefix."""
        _scaffold(tmp_path,
            config_toml=textwrap.dedent("""\
                [generation]
                model = "test-model"

                [composition]
                parts = ["prompts/main", "inputs"]
            """),
            slots={"main": {"default": "base", "variations": {"base": "X"}}},
            inputs={"case1": "Y"},
        )
        pg = load_playground(tmp_path)
        spec = build_run_spec(pg, {"main": "base"}, pg["inputs"][0])

        td = spec["toml_dict"]
        for entry in td["prompts"]:
            assert entry["file"].startswith("../../")


# ---------------------------------------------------------------------------
# build_run_spec — multi-message mode
# ---------------------------------------------------------------------------

class TestBuildRunSpecMultiMessage:
    def test_multi_message_roles(self, tmp_path):
        _scaffold(tmp_path,
            config_toml=textwrap.dedent("""\
                [generation]
                model = "test-model"

                [[composition.messages]]
                role = "system"
                parts = ["prompts/system"]

                [[composition.messages]]
                role = "user"
                parts = ["prompts/main", "inputs"]
            """),
            slots={
                "system": {"default": "base", "variations": {"base": "You are helpful."}},
                "main": {"default": "base", "variations": {"base": "Analyze:"}},
            },
            inputs={"case1": "Data here."},
        )
        pg = load_playground(tmp_path)
        spec = build_run_spec(pg, {"system": "base", "main": "base"}, pg["inputs"][0])

        assert spec["system"] == "You are helpful."
        assert "Analyze:" in spec["user_message"]
        assert "Data here." in spec["user_message"]

        # Check TOML has correct roles
        td = spec["toml_dict"]
        roles = [e["role"] for e in td["prompts"]]
        assert "system" in roles
        assert "user" in roles

    def test_multi_message_substitute(self, tmp_path):
        _scaffold(tmp_path,
            config_toml=textwrap.dedent("""\
                [generation]
                model = "test-model"

                [[composition.messages]]
                role = "user"
                parts = ["prompts/main", "inputs"]
                substitute = true
            """),
            slots={"main": {"default": "base", "variations": {"base": "Process: {{input}}"}}},
            inputs={"case1": "Test data."},
        )
        pg = load_playground(tmp_path)
        spec = build_run_spec(pg, {"main": "base"}, pg["inputs"][0])

        td = spec["toml_dict"]
        assert "vars" in td
        assert len(td["prompts"]) == 1  # Only template, not input


# ---------------------------------------------------------------------------
# Slot resolution
# ---------------------------------------------------------------------------

class TestSlotResolution:
    def test_directory_resolves_to_variation(self, tmp_path):
        _scaffold(tmp_path,
            config_toml=textwrap.dedent("""\
                [generation]
                model = "test-model"

                [composition]
                parts = ["prompts/main", "inputs"]
            """),
            slots={"main": {"default": "base", "variations": {
                "base": "Base prompt.",
                "concise": "Concise prompt.",
            }}},
            inputs={"case1": "Input."},
        )
        pg = load_playground(tmp_path)

        spec_base = build_run_spec(pg, {"main": "base"}, pg["inputs"][0])
        assert "Base prompt." in spec_base["user_message"]

        spec_concise = build_run_spec(pg, {"main": "concise"}, pg["inputs"][0])
        assert "Concise prompt." in spec_concise["user_message"]


# ---------------------------------------------------------------------------
# serialize_toml
# ---------------------------------------------------------------------------

class TestSerializeToml:
    def test_basic_round_trip(self):
        config = {
            "generation": {"model": "claude-sonnet-4-6", "temperature": 1.0, "max_tokens": 4096},
            "prompts": [
                {"role": "user", "file": "../../prompts/main/base.md"},
                {"role": "user", "file": "../../inputs/case1.md"},
            ],
        }
        toml_str = serialize_toml(config)
        assert '[generation]' in toml_str
        assert 'model = "claude-sonnet-4-6"' in toml_str
        assert '[[prompts]]' in toml_str
        assert 'role = "user"' in toml_str

    def test_with_vars(self):
        config = {
            "generation": {"model": "test", "temperature": 0.5, "max_tokens": 1000},
            "vars": {"input": "../../inputs/case1.md"},
            "prompts": [{"role": "user", "file": "../../prompts/main/base.md", "substitute": True}],
        }
        toml_str = serialize_toml(config)
        assert '[vars]' in toml_str
        assert 'input = "../../inputs/case1.md"' in toml_str
        assert 'substitute = true' in toml_str

    def test_special_chars_in_string(self):
        config = {
            "generation": {"separator": "\n---\n"},
            "prompts": [],
        }
        toml_str = serialize_toml(config)
        assert 'separator = "\\n---\\n"' in toml_str

    def test_parseable_by_tomllib(self):
        """Serialized TOML should be parseable."""
        import tomllib

        config = {
            "generation": {"model": "claude-sonnet-4-6", "temperature": 1.0, "max_tokens": 4096},
            "vars": {"input": "../../inputs/case1.md"},
            "prompts": [
                {"role": "user", "file": "../../prompts/main/base.md", "substitute": True},
            ],
        }
        toml_str = serialize_toml(config)
        parsed = tomllib.loads(toml_str)
        assert parsed["generation"]["model"] == "claude-sonnet-4-6"
        assert parsed["vars"]["input"] == "../../inputs/case1.md"
        assert parsed["prompts"][0]["substitute"] is True


# ---------------------------------------------------------------------------
# Multi-variation output structure
# ---------------------------------------------------------------------------

class TestOutputStructure:
    """Test that variation combos produce correct combo labels."""

    def test_single_combo_label(self):
        combo = {"main": "base"}
        parts = [f"{k}={v}" for k, v in sorted(combo.items())]
        label = ",".join(parts)
        assert label == "main=base"

    def test_multi_combo_label(self):
        combo = {"main": "concise", "system": "strict"}
        parts = [f"{k}={v}" for k, v in sorted(combo.items())]
        label = ",".join(parts)
        assert label == "main=concise,system=strict"
