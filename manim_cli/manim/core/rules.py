"""Global rules configuration system for manim-cli.

Schema v1:
  layout  – spacing, margins, overlap policy
  color   – approved palette, semantic mappings, contrast threshold
  style   – stroke/fill/font/animation timing defaults
  policy  – enforcement mode: warn | strict | fix-ready
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

RULES_SCHEMA_VERSION = "1"
POLICY_MODES = ("warn", "strict", "fix-ready")


# ---------------------------------------------------------------------------
# Sub-schemas
# ---------------------------------------------------------------------------

@dataclass
class LayoutRules:
    min_spacing: float = 0.5
    frame_margin: float = 0.5
    overlap_policy: str = "warn"
    max_bbox_intersection_ratio: float = 0.0
    axis_label_padding: float = 0.2
    sample_frames_per_animation: int = 8


@dataclass
class ColorRules:
    approved_palette: list[str] = field(default_factory=list)
    semantic_mappings: dict[str, str] = field(default_factory=dict)
    contrast_threshold: float = 4.5


@dataclass
class StyleRules:
    stroke_width: float = 2.0
    fill_opacity: float = 1.0
    font_size: int = 24
    animation_run_time: float = 1.0


@dataclass
class GlobalRules:
    layout: LayoutRules = field(default_factory=LayoutRules)
    color: ColorRules = field(default_factory=ColorRules)
    style: StyleRules = field(default_factory=StyleRules)
    policy: str = "warn"
    schema_version: str = RULES_SCHEMA_VERSION

    def summary(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "policy": self.policy,
            "layout": asdict(self.layout),
            "color": asdict(self.color),
            "style": asdict(self.style),
        }


# ---------------------------------------------------------------------------
# Loader and validation
# ---------------------------------------------------------------------------

class RulesValidationError(ValueError):
    pass


def _merge_layout(base: LayoutRules, override: dict[str, Any]) -> LayoutRules:
    return LayoutRules(
        min_spacing=float(override.get("min_spacing", base.min_spacing)),
        frame_margin=float(override.get("frame_margin", base.frame_margin)),
        overlap_policy=str(override.get("overlap_policy", base.overlap_policy)),
        max_bbox_intersection_ratio=float(
            override.get("max_bbox_intersection_ratio", base.max_bbox_intersection_ratio)
        ),
        axis_label_padding=float(override.get("axis_label_padding", base.axis_label_padding)),
        sample_frames_per_animation=int(
            override.get("sample_frames_per_animation", base.sample_frames_per_animation)
        ),
    )


def _merge_color(base: ColorRules, override: dict[str, Any]) -> ColorRules:
    return ColorRules(
        approved_palette=list(override.get("approved_palette", base.approved_palette)),
        semantic_mappings=dict(override.get("semantic_mappings", base.semantic_mappings)),
        contrast_threshold=float(override.get("contrast_threshold", base.contrast_threshold)),
    )


def _merge_style(base: StyleRules, override: dict[str, Any]) -> StyleRules:
    return StyleRules(
        stroke_width=float(override.get("stroke_width", base.stroke_width)),
        fill_opacity=float(override.get("fill_opacity", base.fill_opacity)),
        font_size=int(override.get("font_size", base.font_size)),
        animation_run_time=float(override.get("animation_run_time", base.animation_run_time)),
    )


def _validate(rules: GlobalRules) -> None:
    if rules.policy not in POLICY_MODES:
        raise RulesValidationError(
            f"invalid policy mode '{rules.policy}'; expected one of {POLICY_MODES}"
        )
    if rules.layout.min_spacing < 0:
        raise RulesValidationError("layout.min_spacing must be >= 0")
    if rules.layout.frame_margin < 0:
        raise RulesValidationError("layout.frame_margin must be >= 0")
    if rules.layout.max_bbox_intersection_ratio < 0:
        raise RulesValidationError("layout.max_bbox_intersection_ratio must be >= 0")
    if rules.layout.axis_label_padding < 0:
        raise RulesValidationError("layout.axis_label_padding must be >= 0")
    if rules.layout.sample_frames_per_animation < 1:
        raise RulesValidationError("layout.sample_frames_per_animation must be >= 1")
    if not (0.0 <= rules.style.fill_opacity <= 1.0):
        raise RulesValidationError("style.fill_opacity must be in [0.0, 1.0]")
    if rules.style.stroke_width < 0:
        raise RulesValidationError("style.stroke_width must be >= 0")
    if rules.style.font_size < 1:
        raise RulesValidationError("style.font_size must be >= 1")
    if rules.style.animation_run_time <= 0:
        raise RulesValidationError("style.animation_run_time must be > 0")


def load_rules(path: str | None) -> GlobalRules:
    """Load and merge rules config from *path* over defaults.

    Returns default GlobalRules when *path* is None.
    Raises RulesValidationError on schema or value problems.
    """
    base = GlobalRules()
    if path is None:
        return base

    config_path = Path(path)
    if not config_path.exists():
        raise RulesValidationError(f"rules config file not found: {path}")

    try:
        raw = json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RulesValidationError(f"rules config is not valid JSON: {exc}") from exc

    if not isinstance(raw, dict):
        raise RulesValidationError("rules config must be a JSON object")

    schema_ver = raw.get("schema_version", RULES_SCHEMA_VERSION)
    if str(schema_ver) != RULES_SCHEMA_VERSION:
        raise RulesValidationError(
            f"unsupported rules schema_version '{schema_ver}'; expected '{RULES_SCHEMA_VERSION}'"
        )

    layout = _merge_layout(base.layout, raw.get("layout", {}))
    color = _merge_color(base.color, raw.get("color", {}))
    style = _merge_style(base.style, raw.get("style", {}))
    policy = str(raw.get("policy", base.policy))

    rules = GlobalRules(layout=layout, color=color, style=style, policy=policy)
    _validate(rules)
    return rules


def default_rules() -> GlobalRules:
    return GlobalRules()
