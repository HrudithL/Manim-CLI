import json
from pathlib import Path

import pytest

from manim_cli.manim.core.rules import (
    GlobalRules,
    RulesValidationError,
    StyleRules,
    ColorRules,
    LayoutRules,
    default_rules,
    load_rules,
)


# ---------------------------------------------------------------------------
# Default rules
# ---------------------------------------------------------------------------

def test_default_rules_returns_valid_instance() -> None:
    rules = default_rules()
    assert isinstance(rules, GlobalRules)
    assert rules.policy == "warn"
    assert rules.schema_version == "1"


def test_default_rules_summary_has_all_sections() -> None:
    s = default_rules().summary()
    for key in ("schema_version", "policy", "layout", "color", "style"):
        assert key in s


# ---------------------------------------------------------------------------
# load_rules: None path returns defaults
# ---------------------------------------------------------------------------

def test_load_rules_none_returns_defaults() -> None:
    rules = load_rules(None)
    assert rules.policy == "warn"
    assert rules.style.font_size == 24


# ---------------------------------------------------------------------------
# load_rules: merge overrides defaults
# ---------------------------------------------------------------------------

def test_load_rules_overrides_policy(tmp_path: Path) -> None:
    cfg = tmp_path / "rules.json"
    cfg.write_text('{"schema_version": "1", "policy": "strict"}', encoding="utf-8")
    rules = load_rules(str(cfg))
    assert rules.policy == "strict"


def test_load_rules_overrides_style(tmp_path: Path) -> None:
    cfg = tmp_path / "rules.json"
    cfg.write_text('{"schema_version": "1", "style": {"font_size": 48, "animation_run_time": 2.0}}', encoding="utf-8")
    rules = load_rules(str(cfg))
    assert rules.style.font_size == 48
    assert rules.style.animation_run_time == 2.0
    # Non-overridden fields retain defaults
    assert rules.style.stroke_width == 2.0


def test_load_rules_overrides_color(tmp_path: Path) -> None:
    cfg = tmp_path / "rules.json"
    cfg.write_text('{"schema_version": "1", "color": {"approved_palette": ["BLUE", "GREEN"]}}', encoding="utf-8")
    rules = load_rules(str(cfg))
    assert rules.color.approved_palette == ["BLUE", "GREEN"]


def test_load_rules_overrides_layout(tmp_path: Path) -> None:
    cfg = tmp_path / "rules.json"
    cfg.write_text('{"schema_version": "1", "layout": {"min_spacing": 1.0, "frame_margin": 0.25}}', encoding="utf-8")
    rules = load_rules(str(cfg))
    assert rules.layout.min_spacing == 1.0
    assert rules.layout.frame_margin == 0.25


# ---------------------------------------------------------------------------
# load_rules: validation errors
# ---------------------------------------------------------------------------

def test_load_rules_missing_file_raises() -> None:
    with pytest.raises(RulesValidationError, match="not found"):
        load_rules("/nonexistent/rules.json")


def test_load_rules_invalid_json_raises(tmp_path: Path) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text("not json {{{", encoding="utf-8")
    with pytest.raises(RulesValidationError, match="not valid JSON"):
        load_rules(str(bad))


def test_load_rules_non_object_raises(tmp_path: Path) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text("[1, 2, 3]", encoding="utf-8")
    with pytest.raises(RulesValidationError, match="JSON object"):
        load_rules(str(bad))


def test_load_rules_invalid_policy_raises(tmp_path: Path) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text('{"policy": "turbo"}', encoding="utf-8")
    with pytest.raises(RulesValidationError, match="policy"):
        load_rules(str(bad))


def test_load_rules_negative_min_spacing_raises(tmp_path: Path) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text('{"layout": {"min_spacing": -1}}', encoding="utf-8")
    with pytest.raises(RulesValidationError, match="min_spacing"):
        load_rules(str(bad))


def test_load_rules_bad_fill_opacity_raises(tmp_path: Path) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text('{"style": {"fill_opacity": 2.0}}', encoding="utf-8")
    with pytest.raises(RulesValidationError, match="fill_opacity"):
        load_rules(str(bad))


def test_load_rules_wrong_schema_version_raises(tmp_path: Path) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text('{"schema_version": "99"}', encoding="utf-8")
    with pytest.raises(RulesValidationError, match="schema_version"):
        load_rules(str(bad))


# ---------------------------------------------------------------------------
# fix-ready is a valid policy
# ---------------------------------------------------------------------------

def test_load_rules_fix_ready_policy_valid(tmp_path: Path) -> None:
    cfg = tmp_path / "rules.json"
    cfg.write_text('{"policy": "fix-ready"}', encoding="utf-8")
    rules = load_rules(str(cfg))
    assert rules.policy == "fix-ready"
