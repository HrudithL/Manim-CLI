import json
import subprocess
import sys
from pathlib import Path

from manim_cli.manim._meta import MANIM_CE_VERIFIED_VERSION
from manim_cli.manim.utils.output import ENVELOPE_SCHEMA_VERSION


def _run_cli(*args: str) -> subprocess.CompletedProcess:
    cmd = [sys.executable, "-m", "manim_cli.manim.cli", *args]
    return subprocess.run(cmd, text=True, capture_output=True, check=False)


# ---------------------------------------------------------------------------
# Version
# ---------------------------------------------------------------------------

def test_cli_version_via_subprocess() -> None:
    proc = _run_cli("--version")
    assert proc.returncode == 0, proc.stderr
    assert "Manim CE last verified:" in proc.stdout
    assert MANIM_CE_VERIFIED_VERSION in proc.stdout


# ---------------------------------------------------------------------------
# JSON envelope contract: stable keys on every --json response
# ---------------------------------------------------------------------------

def test_json_envelope_has_required_keys(tmp_path: Path) -> None:
    scene_file = tmp_path / "demo_scene.py"
    scene_file.write_text(
        "from manim import Scene\nclass S(Scene): pass\n",
        encoding="utf-8",
    )
    proc = _run_cli("--json", "scene", "list", "--repo-path", str(tmp_path))
    assert proc.returncode == 0, proc.stderr
    data = json.loads(proc.stdout)
    for key in ("ok", "schema_version", "command", "timestamp"):
        assert key in data, f"missing key '{key}' in envelope"
    assert data["schema_version"] == ENVELOPE_SCHEMA_VERSION
    assert data["command"] == "scene list"


def test_cli_json_scene_list_via_subprocess(tmp_path: Path) -> None:
    scene_file = tmp_path / "demo_scene.py"
    scene_file.write_text(
        "from manim import Scene\nclass ExampleScene(Scene): pass\n",
        encoding="utf-8",
    )
    proc = _run_cli("--json", "scene", "list", "--repo-path", str(tmp_path))
    assert proc.returncode == 0, proc.stderr
    data = json.loads(proc.stdout)
    assert data["ok"] is True
    assert data["count"] == 1
    assert data["scenes"][0]["name"] == "ExampleScene"


# ---------------------------------------------------------------------------
# Non-interactive REPL guard
# ---------------------------------------------------------------------------

def test_no_subcommand_json_returns_repl_blocked() -> None:
    """--json with no subcommand must never hang; returns NON_INTERACTIVE_REPL_BLOCKED."""
    proc = _run_cli("--json")
    data = json.loads(proc.stdout)
    assert data["ok"] is False
    assert data["error_code"] == "NON_INTERACTIVE_REPL_BLOCKED"
    assert proc.returncode != 0


def test_no_subcommand_piped_stdin_blocks_repl() -> None:
    """Piped stdin (non-tty) with no subcommand must not start REPL."""
    proc = subprocess.run(
        [sys.executable, "-m", "manim_cli.manim.cli"],
        input="",
        text=True,
        capture_output=True,
        check=False,
    )
    # Should exit non-zero and not block
    assert proc.returncode != 0
    # JSON envelope emitted on stdout
    data = json.loads(proc.stdout)
    assert data["error_code"] == "NON_INTERACTIVE_REPL_BLOCKED"


# ---------------------------------------------------------------------------
# Rules config loading
# ---------------------------------------------------------------------------

def test_invalid_rules_config_returns_error(tmp_path: Path) -> None:
    bad_rules = tmp_path / "rules.json"
    bad_rules.write_text('{"policy": "invalid_mode"}', encoding="utf-8")
    scene_file = tmp_path / "s.py"
    scene_file.write_text("from manim import Scene\nclass S(Scene): pass\n", encoding="utf-8")

    proc = _run_cli("--json", "--rules-config", str(bad_rules), "scene", "list", "--repo-path", str(tmp_path))
    data = json.loads(proc.stdout)
    assert data["ok"] is False
    assert data["error_code"] == "RULES_LOAD_ERROR"


def test_valid_rules_config_is_accepted(tmp_path: Path) -> None:
    rules_file = tmp_path / "rules.json"
    rules_file.write_text(
        '{"schema_version": "1", "policy": "warn", "style": {"font_size": 30}}',
        encoding="utf-8",
    )
    scene_file = tmp_path / "s.py"
    scene_file.write_text("from manim import Scene\nclass S(Scene): pass\n", encoding="utf-8")

    proc = _run_cli("--json", "--rules-config", str(rules_file), "scene", "list", "--repo-path", str(tmp_path))
    assert proc.returncode == 0, proc.stderr
    data = json.loads(proc.stdout)
    assert data["ok"] is True


# ---------------------------------------------------------------------------
# project init outputs active_rules
# ---------------------------------------------------------------------------

def test_project_init_includes_active_rules(tmp_path: Path) -> None:
    target = tmp_path / "proj"
    proc = _run_cli("--json", "project", "init", "--target-dir", str(target))
    assert proc.returncode == 0, proc.stderr
    data = json.loads(proc.stdout)
    assert data["ok"] is True
    assert "active_rules" in data
    assert "policy" in data["active_rules"]


def test_project_init_template_uses_rule_constants(tmp_path: Path) -> None:
    target = tmp_path / "proj"
    proc = _run_cli("--json", "project", "init", "--target-dir", str(target))
    assert proc.returncode == 0
    scene_py = target / "scene.py"
    content = scene_py.read_text(encoding="utf-8")
    assert "STROKE_WIDTH" in content
    assert "FONT_SIZE" in content
    assert "ANIMATION_RUN_TIME" in content


# ---------------------------------------------------------------------------
# validate scene-style command
# ---------------------------------------------------------------------------

def test_validate_scene_style_clean_scene(tmp_path: Path) -> None:
    scene_file = tmp_path / "clean.py"
    scene_file.write_text(
        "from manim import *\nclass Clean(Scene):\n    def construct(self):\n        pass\n",
        encoding="utf-8",
    )
    proc = _run_cli("--json", "validate", "scene-style", "--scene-file", str(scene_file))
    assert proc.returncode == 0, proc.stderr
    data = json.loads(proc.stdout)
    assert data["ok"] is True
    assert data["command"] == "validate scene-style"
    assert "diagnostics" in data
    assert "effective_rules" in data


def test_validate_scene_style_missing_file(tmp_path: Path) -> None:
    proc = _run_cli("--json", "validate", "scene-style", "--scene-file", str(tmp_path / "missing.py"))
    data = json.loads(proc.stdout)
    assert data["ok"] is False
    assert data["error_code"] in ("FILE_NOT_FOUND", "POLICY_VIOLATION")


def test_validate_scene_style_strict_warns(tmp_path: Path) -> None:
    rules_file = tmp_path / "rules.json"
    rules_file.write_text(
        '{"schema_version": "1", "policy": "strict", "color": {"approved_palette": ["BLUE"]}}',
        encoding="utf-8",
    )
    scene_file = tmp_path / "scene.py"
    scene_file.write_text(
        "from manim import *\nclass S(Scene):\n    def construct(self):\n        c = Circle(color=RED)\n        self.add(c)\n",
        encoding="utf-8",
    )
    proc = _run_cli("--json", "--rules-config", str(rules_file), "validate", "scene-style", "--scene-file", str(scene_file))
    data = json.loads(proc.stdout)
    assert data["ok"] is False
    assert data["error_code"] == "POLICY_VIOLATION"
    assert len(data["diagnostics"]) > 0


def test_validate_scene_layout_command_strict_blocks(tmp_path: Path) -> None:
    rules_file = tmp_path / "rules.json"
    rules_file.write_text(
        '{"schema_version": "1", "policy": "strict"}',
        encoding="utf-8",
    )
    scene_file = tmp_path / "layout_bad.py"
    scene_file.write_text(
        "from manim import *\nclass S(Scene):\n    def construct(self):\n        t = Text('x')\n        self.add(t)\n",
        encoding="utf-8",
    )
    proc = _run_cli(
        "--json",
        "--rules-config",
        str(rules_file),
        "validate",
        "scene-layout",
        "--scene-file",
        str(scene_file),
    )
    data = json.loads(proc.stdout)
    assert data["ok"] is False
    assert data["command"] == "validate scene-layout"
    assert data["error_code"] == "POLICY_VIOLATION"
    diag_ids = {d["rule_id"] for d in data["diagnostics"]}
    assert "layout.unpositioned_add" in diag_ids


# ---------------------------------------------------------------------------
# analyze scene-file includes policy_facts
# ---------------------------------------------------------------------------

def test_analyze_includes_policy_facts(tmp_path: Path) -> None:
    scene_file = tmp_path / "s.py"
    scene_file.write_text(
        "from manim import *\nclass S(Scene):\n    def construct(self):\n        t = Text('hi', color=RED)\n        self.play(Write(t))\n",
        encoding="utf-8",
    )
    proc = _run_cli("--json", "analyze", "scene-file", "--scene-file", str(scene_file))
    assert proc.returncode == 0, proc.stderr
    data = json.loads(proc.stdout)
    assert data["ok"] is True
    assert "policy_facts" in data
    pf = data["policy_facts"]
    assert "color_constants" in pf
    assert "overlap_risk_score" in pf


# ---------------------------------------------------------------------------
# render run --dry-run: envelope + diagnostics
# ---------------------------------------------------------------------------

def test_render_dry_run_json_output(tmp_path: Path) -> None:
    scene_file = tmp_path / "scene.py"
    scene_file.write_text(
        "from manim import *\nclass DryRunScene(Scene):\n    def construct(self):\n        self.play(Write(Text('x')))\n",
        encoding="utf-8",
    )
    proc = _run_cli(
        "--json", "render", "run",
        "--scene-file", str(scene_file),
        "--scene-name", "DryRunScene",
        "--quality", "l",
        "--dry-run",
    )
    assert proc.returncode == 0, proc.stderr
    data = json.loads(proc.stdout)
    assert data["ok"] is True
    assert data["dry_run"] is True
    assert "-ql" in data["render_command"]
    assert "diagnostics" in data
    assert "render_command" in data
    assert data["schema_version"] == ENVELOPE_SCHEMA_VERSION


# ---------------------------------------------------------------------------
# Scene list is sorted / deterministic
# ---------------------------------------------------------------------------

def test_scene_list_is_sorted(tmp_path: Path) -> None:
    for name in ("ZScene", "AScene", "MScene"):
        f = tmp_path / f"{name.lower()}.py"
        f.write_text(f"from manim import Scene\nclass {name}(Scene): pass\n", encoding="utf-8")

    proc = _run_cli("--json", "scene", "list", "--repo-path", str(tmp_path))
    data = json.loads(proc.stdout)
    names = [s["name"] for s in data["scenes"]]
    assert names == sorted(names)
