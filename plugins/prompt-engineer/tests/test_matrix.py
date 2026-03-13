"""Tests for lib/matrix.py — config loading, matrix expansion, and edge cases."""

import os
import sys
import textwrap
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))

from matrix import (
    _ensure_list,
    _resolve_prompt_entry,
    expand_matrix,
    load_config,
    matrix_dimensions,
    resolve_value,
)


# ---------------------------------------------------------------------------
# _ensure_list
# ---------------------------------------------------------------------------

class TestEnsureList:
    def test_scalar_string(self):
        assert _ensure_list("hello") == ["hello"]

    def test_scalar_int(self):
        assert _ensure_list(42) == [42]

    def test_scalar_float(self):
        assert _ensure_list(0.5) == [0.5]

    def test_list_passthrough(self):
        assert _ensure_list([1, 2, 3]) == [1, 2, 3]

    def test_empty_list(self):
        assert _ensure_list([]) == []


# ---------------------------------------------------------------------------
# resolve_value
# ---------------------------------------------------------------------------

class TestResolveValue:
    def test_reads_file(self, tmp_path):
        f = tmp_path / "prompt.md"
        f.write_text("hello world", encoding="utf-8")
        assert resolve_value("prompt.md", tmp_path) == "hello world"

    def test_missing_file(self, tmp_path):
        with pytest.raises(FileNotFoundError, match="nope.md"):
            resolve_value("nope.md", tmp_path)

    def test_relative_to_base_dir(self, tmp_path):
        sub = tmp_path / "sub"
        sub.mkdir()
        f = sub / "deep.txt"
        f.write_text("deep content", encoding="utf-8")
        assert resolve_value("sub/deep.txt", tmp_path) == "deep content"


# ---------------------------------------------------------------------------
# _resolve_prompt_entry
# ---------------------------------------------------------------------------

class TestResolvePromptEntry:
    def test_inline_scalar(self, tmp_path):
        entry = {"role": "user", "prompt": "say hi"}
        result = _resolve_prompt_entry(entry, tmp_path)
        assert result == [("say hi", "say hi")]

    def test_inline_array(self, tmp_path):
        entry = {"role": "user", "prompt": ["hello", "goodbye"]}
        result = _resolve_prompt_entry(entry, tmp_path)
        assert len(result) == 2
        assert result[0] == ("hello", "hello")
        assert result[1] == ("goodbye", "goodbye")

    def test_file_scalar(self, tmp_path):
        (tmp_path / "q.md").write_text("question?", encoding="utf-8")
        entry = {"role": "user", "file": "q.md"}
        result = _resolve_prompt_entry(entry, tmp_path)
        assert result == [("q.md", "question?")]

    def test_file_array(self, tmp_path):
        (tmp_path / "a.md").write_text("aaa", encoding="utf-8")
        (tmp_path / "b.md").write_text("bbb", encoding="utf-8")
        entry = {"role": "system", "file": ["a.md", "b.md"]}
        result = _resolve_prompt_entry(entry, tmp_path)
        assert result == [("a.md", "aaa"), ("b.md", "bbb")]

    def test_both_file_and_prompt_errors(self, tmp_path):
        entry = {"role": "user", "file": "x.md", "prompt": "inline"}
        with pytest.raises(ValueError, match="both"):
            _resolve_prompt_entry(entry, tmp_path)

    def test_neither_file_nor_prompt_errors(self, tmp_path):
        entry = {"role": "user"}
        with pytest.raises(ValueError, match="missing"):
            _resolve_prompt_entry(entry, tmp_path)

    def test_long_inline_label_truncated(self, tmp_path):
        long = "a" * 50
        entry = {"role": "user", "prompt": long}
        result = _resolve_prompt_entry(entry, tmp_path)
        label = result[0][0]
        assert len(label) == 30
        assert label.endswith("...")

    def test_missing_file_in_entry(self, tmp_path):
        entry = {"role": "user", "file": "ghost.md"}
        with pytest.raises(FileNotFoundError, match="ghost.md"):
            _resolve_prompt_entry(entry, tmp_path)


# ---------------------------------------------------------------------------
# expand_matrix
# ---------------------------------------------------------------------------

def _config(tmp_path, generation=None, prompts=None, output=None):
    """Helper to build a config dict with _base_dir set."""
    cfg = {"_base_dir": tmp_path}
    if generation is not None:
        cfg["generation"] = generation
    if prompts is not None:
        cfg["prompts"] = prompts
    if output is not None:
        cfg["output"] = output
    return cfg


class TestExpandMatrix:
    def test_single_run_inline(self, tmp_path):
        cfg = _config(tmp_path,
            generation={"model": "m1", "temperature": 0.5},
            prompts=[{"role": "user", "prompt": "hi"}],
        )
        runs = expand_matrix(cfg)
        assert len(runs) == 1
        r = runs[0]
        assert r["user_message"] == "hi"
        assert r["system"] is None
        assert r["model"] == "m1"
        assert r["temperature"] == 0.5
        assert r["max_tokens"] == 4096

    def test_model_sweep(self, tmp_path):
        cfg = _config(tmp_path,
            generation={"model": ["m1", "m2"]},
            prompts=[{"role": "user", "prompt": "hi"}],
        )
        runs = expand_matrix(cfg)
        assert len(runs) == 2
        assert runs[0]["model"] == "m1"
        assert runs[1]["model"] == "m2"

    def test_temperature_sweep(self, tmp_path):
        cfg = _config(tmp_path,
            generation={"temperature": [0.0, 0.5, 1.0]},
            prompts=[{"role": "user", "prompt": "hi"}],
        )
        runs = expand_matrix(cfg)
        assert len(runs) == 3
        assert [r["temperature"] for r in runs] == [0.0, 0.5, 1.0]

    def test_full_cartesian_product(self, tmp_path):
        cfg = _config(tmp_path,
            generation={"model": ["m1", "m2"], "temperature": [0.0, 1.0]},
            prompts=[
                {"role": "system", "prompt": ["strict", "relaxed"]},
                {"role": "user", "prompt": "hi"},
            ],
        )
        runs = expand_matrix(cfg)
        # 2 models × 2 temps × 2 system prompts × 1 user = 8
        assert len(runs) == 8

    def test_multiple_user_entries_concatenated(self, tmp_path):
        cfg = _config(tmp_path,
            prompts=[
                {"role": "user", "prompt": "part1"},
                {"role": "user", "prompt": "part2"},
            ],
        )
        runs = expand_matrix(cfg)
        assert len(runs) == 1
        assert runs[0]["user_message"] == "part1\n\npart2"
        assert runs[0]["labels"]["user"] == "part1+part2"

    def test_multiple_system_entries_concatenated(self, tmp_path):
        cfg = _config(tmp_path,
            prompts=[
                {"role": "system", "prompt": "role"},
                {"role": "system", "prompt": "rules"},
                {"role": "user", "prompt": "question"},
            ],
        )
        runs = expand_matrix(cfg)
        assert len(runs) == 1
        assert runs[0]["system"] == "role\n\nrules"
        assert runs[0]["labels"]["system"] == "role/rules"

    def test_file_prompts(self, tmp_path):
        (tmp_path / "sys.md").write_text("be helpful", encoding="utf-8")
        (tmp_path / "q.md").write_text("what is 2+2?", encoding="utf-8")
        cfg = _config(tmp_path,
            prompts=[
                {"role": "system", "file": "sys.md"},
                {"role": "user", "file": "q.md"},
            ],
        )
        runs = expand_matrix(cfg)
        assert len(runs) == 1
        assert runs[0]["system"] == "be helpful"
        assert runs[0]["user_message"] == "what is 2+2?"
        assert runs[0]["labels"]["system"] == "sys.md"
        assert runs[0]["labels"]["user"] == "q.md"

    def test_file_array_sweep(self, tmp_path):
        (tmp_path / "a.md").write_text("aaa", encoding="utf-8")
        (tmp_path / "b.md").write_text("bbb", encoding="utf-8")
        cfg = _config(tmp_path,
            prompts=[
                {"role": "system", "file": ["a.md", "b.md"]},
                {"role": "user", "prompt": "go"},
            ],
        )
        runs = expand_matrix(cfg)
        assert len(runs) == 2
        assert runs[0]["system"] == "aaa"
        assert runs[1]["system"] == "bbb"

    def test_no_prompts_section_errors(self, tmp_path):
        cfg = _config(tmp_path, generation={"model": "m1"})
        with pytest.raises(ValueError, match="missing.*prompts"):
            expand_matrix(cfg)

    def test_no_user_prompts_errors(self, tmp_path):
        cfg = _config(tmp_path,
            prompts=[{"role": "system", "prompt": "sys only"}],
        )
        with pytest.raises(ValueError, match="no user prompts"):
            expand_matrix(cfg)

    def test_unknown_role_errors(self, tmp_path):
        cfg = _config(tmp_path,
            prompts=[{"role": "assistant", "prompt": "bad"}],
        )
        with pytest.raises(ValueError, match="Unknown prompt role"):
            expand_matrix(cfg)

    def test_defaults_when_generation_missing(self, tmp_path):
        cfg = _config(tmp_path,
            prompts=[{"role": "user", "prompt": "hi"}],
        )
        runs = expand_matrix(cfg)
        assert len(runs) == 1
        assert runs[0]["model"] == "claude-sonnet-4-6"
        assert runs[0]["temperature"] == 1.0
        assert runs[0]["max_tokens"] == 4096


# ---------------------------------------------------------------------------
# matrix_dimensions
# ---------------------------------------------------------------------------

class TestMatrixDimensions:
    def test_single_run(self, tmp_path):
        cfg = _config(tmp_path,
            generation={"model": "m1", "temperature": 0.5},
            prompts=[{"role": "user", "prompt": "hi"}],
        )
        info = matrix_dimensions(cfg)
        assert info["total_runs"] == 1
        assert info["dimensions"] == {}

    def test_sweep_dimensions_reported(self, tmp_path):
        cfg = _config(tmp_path,
            generation={"model": ["m1", "m2"], "temperature": [0.0, 1.0]},
            prompts=[
                {"role": "system", "prompt": ["strict", "relaxed"]},
                {"role": "user", "prompt": "hi"},
            ],
        )
        info = matrix_dimensions(cfg)
        assert info["total_runs"] == 8
        assert "model" in info["dimensions"]
        assert "temperature" in info["dimensions"]
        assert "system.prompt" in info["dimensions"]

    def test_no_sweep_no_dimensions(self, tmp_path):
        cfg = _config(tmp_path,
            prompts=[{"role": "user", "prompt": "hi"}],
        )
        info = matrix_dimensions(cfg)
        assert info["dimensions"] == {}
        assert info["total_runs"] == 1


# ---------------------------------------------------------------------------
# load_config (integration — round-trip through TOML)
# ---------------------------------------------------------------------------

class TestLoadConfig:
    def test_basic_toml(self, tmp_path):
        toml = tmp_path / "run.toml"
        toml.write_text(textwrap.dedent("""\
            [generation]
            model = "test-model"
            temperature = 0.5

            [[prompts]]
            role = "user"
            prompt = "hello"
        """), encoding="utf-8")

        cfg = load_config(str(toml))
        assert cfg["generation"]["model"] == "test-model"
        assert cfg["generation"]["temperature"] == 0.5
        assert len(cfg["prompts"]) == 1
        assert cfg["prompts"][0]["role"] == "user"
        assert cfg["_base_dir"] == tmp_path

    def test_array_values_in_toml(self, tmp_path):
        toml = tmp_path / "sweep.toml"
        toml.write_text(textwrap.dedent("""\
            [generation]
            model = ["m1", "m2"]
            temperature = [0.0, 1.0]

            [[prompts]]
            role = "system"
            prompt = ["strict", "relaxed"]

            [[prompts]]
            role = "user"
            prompt = "go"
        """), encoding="utf-8")

        cfg = load_config(str(toml))
        assert cfg["generation"]["model"] == ["m1", "m2"]
        assert cfg["generation"]["temperature"] == [0.0, 1.0]
        assert cfg["prompts"][0]["prompt"] == ["strict", "relaxed"]

    def test_file_references_resolved_relative(self, tmp_path):
        (tmp_path / "sys.md").write_text("system text", encoding="utf-8")
        (tmp_path / "usr.md").write_text("user text", encoding="utf-8")
        toml = tmp_path / "run.toml"
        toml.write_text(textwrap.dedent("""\
            [[prompts]]
            role = "system"
            file = "sys.md"

            [[prompts]]
            role = "user"
            file = "usr.md"
        """), encoding="utf-8")

        cfg = load_config(str(toml))
        runs = expand_matrix(cfg)
        assert runs[0]["system"] == "system text"
        assert runs[0]["user_message"] == "user text"

    def test_output_section(self, tmp_path):
        toml = tmp_path / "run.toml"
        toml.write_text(textwrap.dedent("""\
            [[prompts]]
            role = "user"
            prompt = "hi"

            [output]
            file = "results.jsonl"
        """), encoding="utf-8")

        cfg = load_config(str(toml))
        assert cfg["output"]["file"] == "results.jsonl"

    def test_full_round_trip(self, tmp_path):
        (tmp_path / "strict.md").write_text("be strict", encoding="utf-8")
        (tmp_path / "relaxed.md").write_text("be relaxed", encoding="utf-8")
        (tmp_path / "q.md").write_text("question?", encoding="utf-8")

        toml = tmp_path / "matrix.toml"
        toml.write_text(textwrap.dedent("""\
            [generation]
            model = ["m1", "m2"]
            temperature = [0.0, 1.0]
            max_tokens = 100

            [[prompts]]
            role = "system"
            file = ["strict.md", "relaxed.md"]

            [[prompts]]
            role = "user"
            file = "q.md"

            [output]
            file = "out.jsonl"
        """), encoding="utf-8")

        cfg = load_config(str(toml))
        runs = expand_matrix(cfg)
        # 2 models × 2 temps × 2 system files × 1 user = 8
        assert len(runs) == 8

        info = matrix_dimensions(cfg)
        assert info["total_runs"] == 8

        # Spot-check first and last
        assert runs[0]["model"] == "m1"
        assert runs[0]["system"] == "be strict"
        assert runs[0]["labels"]["system"] == "strict.md"
        assert runs[-1]["model"] == "m2"
        assert runs[-1]["system"] == "be relaxed"
