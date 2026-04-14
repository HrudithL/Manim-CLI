from __future__ import annotations

import shlex
import sys
from importlib.metadata import PackageNotFoundError, version as pkg_version

import click

from manim_cli.manim._meta import MANIM_CE_VERIFIED_VERSION
from manim_cli.manim.core.analyze import analyze_scene_file
from manim_cli.manim.core.install import install_skills
from manim_cli.manim.core.project import init_project
from manim_cli.manim.core.render import run_render
from manim_cli.manim.core.rules import GlobalRules, RulesValidationError, default_rules, load_rules
from manim_cli.manim.core.scene_index import discover_scenes
from manim_cli.manim.core.validate import validate_repo, validate_scene_layout, validate_scene_style
from manim_cli.manim.utils.output import build_error_envelope, build_envelope, emit

CONTEXT_SETTINGS = {"help_option_names": ["-h", "--help"]}


def _cli_version_message() -> str:
    try:
        dist_version = pkg_version("manim-cli")
    except PackageNotFoundError:
        dist_version = "0.0.0+unknown"
    return (
        f"{dist_version}\n"
        f"Manim CE last verified: {MANIM_CE_VERIFIED_VERSION} "
        "(informational only; not a compatibility guarantee — see README)"
    )


def _get_rules(ctx: click.Context) -> GlobalRules:
    return ctx.obj.get("rules") or default_rules()


def _json_mode(ctx: click.Context) -> bool:
    return ctx.obj.get("json_output", False)


# ---------------------------------------------------------------------------
# Exception normalization: wrap any Click/OS/unknown error in JSON envelope
# ---------------------------------------------------------------------------

def _handle_exception(
    exc: BaseException,
    command: str,
    json_output: bool,
) -> None:
    if isinstance(exc, click.UsageError):
        payload = build_error_envelope(
            command=command,
            error=str(exc),
            error_code="USAGE_ERROR",
        )
    elif isinstance(exc, FileNotFoundError):
        payload = build_error_envelope(
            command=command,
            error=str(exc),
            error_code="FILE_NOT_FOUND",
        )
    elif isinstance(exc, RulesValidationError):
        payload = build_error_envelope(
            command=command,
            error=str(exc),
            error_code="RULES_LOAD_ERROR",
        )
    elif isinstance(exc, click.ClickException):
        payload = build_error_envelope(
            command=command,
            error=exc.format_message(),
            error_code="USAGE_ERROR",
        )
    else:
        payload = build_error_envelope(
            command=command,
            error=str(exc),
            error_code="UNKNOWN_ERROR",
        )
    emit(payload, as_json=json_output)


# ---------------------------------------------------------------------------
# Main group
# ---------------------------------------------------------------------------

@click.group(context_settings=CONTEXT_SETTINGS, invoke_without_command=True)
@click.version_option(
    _cli_version_message(),
    "--version",
    prog_name="manim-cli",
)
@click.option("--json-output", "--json", is_flag=True, default=False, help="Emit JSON output.")
@click.option(
    "--rules-config",
    default=None,
    metavar="PATH",
    help="Path to a JSON rules config file (global policy, style, color, layout).",
    type=click.Path(path_type=str),
)
@click.pass_context
def main(ctx: click.Context, json_output: bool, rules_config: str | None) -> None:
    """Manim CLI harness."""
    ctx.ensure_object(dict)
    ctx.obj["json_output"] = json_output

    # Load rules once and store in context
    try:
        rules = load_rules(rules_config)
    except RulesValidationError as exc:
        if json_output:
            emit(
                build_error_envelope(
                    command="",
                    error=str(exc),
                    error_code="RULES_LOAD_ERROR",
                ),
                as_json=True,
            )
        else:
            click.echo(f"Error loading rules config: {exc}", err=True)
        ctx.exit(1)
        return

    ctx.obj["rules"] = rules
    ctx.obj["rules_config"] = rules_config

    if ctx.invoked_subcommand is None:
        _run_repl(json_output=json_output, rules=rules)


# ---------------------------------------------------------------------------
# REPL (human-only; blocked in non-interactive contexts)
# ---------------------------------------------------------------------------

def _run_repl(json_output: bool, rules: GlobalRules) -> None:
    if json_output or not sys.stdin.isatty():
        emit(
            build_error_envelope(
                command="",
                error=(
                    "no subcommand supplied and stdin is non-interactive; "
                    "REPL is disabled in automation contexts"
                ),
                error_code="NON_INTERACTIVE_REPL_BLOCKED",
            ),
            as_json=True,
        )
        sys.exit(1)

    click.echo("manim-cli REPL. Type 'help' or 'exit'.")
    while True:
        raw = click.prompt("manim>", prompt_suffix=" ", default="", show_default=False)
        cmd = raw.strip()
        if not cmd:
            continue
        if cmd in {"exit", "quit"}:
            click.echo("Goodbye.")
            break
        if cmd == "help":
            click.echo("Use standard command form, e.g.: scene list --repo-path /path/to/manim")
            continue
        args = shlex.split(cmd)
        try:
            main.main(
                args=args,
                prog_name="manim-cli",
                standalone_mode=False,
                obj={"json_output": json_output, "rules": rules},
            )
        except SystemExit:
            continue
        except Exception as exc:  # pragma: no cover - REPL safety net
            emit({"ok": False, "error": str(exc)}, as_json=json_output)


# ---------------------------------------------------------------------------
# project commands
# ---------------------------------------------------------------------------

@main.group()
def project() -> None:
    """Project commands."""


@project.command("init")
@click.option("--target-dir", required=True, type=click.Path(path_type=str))
@click.option("--scene-name", default="HelloScene", show_default=True)
@click.pass_context
def project_init(ctx: click.Context, target_dir: str, scene_name: str) -> None:
    json_output = _json_mode(ctx)
    rules = _get_rules(ctx)
    try:
        result = init_project(target_dir=target_dir, scene_name=scene_name, rules=rules)
        payload = build_envelope(
            ok=result["ok"],
            command="project init",
            payload={k: v for k, v in result.items() if k not in ("ok",)},
        )
        emit(payload, as_json=json_output)
    except Exception as exc:
        _handle_exception(exc, "project init", json_output)


# ---------------------------------------------------------------------------
# install commands
# ---------------------------------------------------------------------------

@main.command("install")
@click.option("--skills", is_flag=True, required=True, help="Install agent skill files into the project.")
@click.option(
    "--agent",
    default="claude",
    type=click.Choice(["claude", "copilot", "generic"], case_sensitive=False),
    show_default=True,
    help="Target agent type.",
)
@click.option("--target", default=None, type=click.Path(path_type=str), help="Override install directory.")
@click.pass_context
def install_cmd(ctx: click.Context, skills: bool, agent: str, target: str | None) -> None:
    json_output = _json_mode(ctx)
    try:
        result = install_skills(agent=agent, target_override=target)
        payload = build_envelope(
            ok=result["ok"],
            command="install",
            payload={k: v for k, v in result.items() if k not in ("ok",)},
        )
        if not result["ok"] and "error_code" in result:
            payload["error_code"] = result["error_code"]
        if "error" in result:
            payload["error"] = result["error"]
        emit(payload, as_json=json_output)
    except Exception as exc:
        _handle_exception(exc, "install", json_output)


# ---------------------------------------------------------------------------
# scene commands
# ---------------------------------------------------------------------------

@main.group()
def scene() -> None:
    """Scene discovery commands."""


@scene.command("list")
@click.option("--repo-path", required=True, type=click.Path(exists=True, path_type=str))
@click.pass_context
def scene_list(ctx: click.Context, repo_path: str) -> None:
    json_output = _json_mode(ctx)
    try:
        scenes = discover_scenes(repo_path)
        scenes_data = sorted([s.__dict__ for s in scenes], key=lambda s: (s.get("file_path", ""), s.get("name", "")))
        payload = build_envelope(
            ok=True,
            command="scene list",
            payload={
                "count": len(scenes_data),
                "scenes": scenes_data,
                "command_args_resolved": {"repo_path": repo_path},
            },
        )
        emit(payload, as_json=json_output)
    except Exception as exc:
        _handle_exception(exc, "scene list", json_output)


# ---------------------------------------------------------------------------
# render commands
# ---------------------------------------------------------------------------

@main.group()
def render() -> None:
    """Render scenes with real Manim."""


@render.command("run")
@click.option("--scene-file", required=True, type=click.Path(exists=True, path_type=str))
@click.option("--scene-name", required=True)
@click.option("--quality", default="l", show_default=True)
@click.option("--renderer", default="cairo", show_default=True)
@click.option("--output-dir", type=click.Path(path_type=str), default=None)
@click.option("--dry-run", is_flag=True, default=False)
@click.pass_context
def render_run(
    ctx: click.Context,
    scene_file: str,
    scene_name: str,
    quality: str,
    renderer: str,
    output_dir: str | None,
    dry_run: bool,
) -> None:
    json_output = _json_mode(ctx)
    rules = _get_rules(ctx)
    try:
        result = run_render(
            scene_file=scene_file,
            scene_name=scene_name,
            quality=quality,
            renderer=renderer,
            output_dir=output_dir,
            dry_run=dry_run,
            rules=rules,
        )
        # Rename 'command' (subprocess argv) to 'render_command' to avoid
        # colliding with the envelope's 'command' (CLI subcommand name).
        inner: dict = {
            k if k != "command" else "render_command": v
            for k, v in result.items()
            if k not in ("ok",)
        }
        payload = build_envelope(
            ok=result["ok"],
            command="render run",
            payload=inner,
        )
        if not result["ok"] and "error_code" in result:
            payload["error_code"] = result["error_code"]
        if "error" in result:
            payload["error"] = result["error"]
        emit(payload, as_json=json_output)
    except Exception as exc:
        _handle_exception(exc, "render run", json_output)


# ---------------------------------------------------------------------------
# analyze commands
# ---------------------------------------------------------------------------

@main.group()
def analyze() -> None:
    """AST analysis commands."""


@analyze.command("scene-file")
@click.option("--scene-file", required=True, type=click.Path(exists=True, path_type=str))
@click.pass_context
def analyze_scene_file_cmd(ctx: click.Context, scene_file: str) -> None:
    json_output = _json_mode(ctx)
    rules = _get_rules(ctx)
    try:
        result = analyze_scene_file(scene_file, rules=rules, include_policy_facts=True)
        payload = build_envelope(
            ok=True,
            command="analyze scene-file",
            payload=result,
        )
        emit(payload, as_json=json_output)
    except FileNotFoundError as exc:
        _handle_exception(exc, "analyze scene-file", json_output)
    except Exception as exc:
        _handle_exception(exc, "analyze scene-file", json_output)


# ---------------------------------------------------------------------------
# validate commands
# ---------------------------------------------------------------------------

@main.group()
def validate() -> None:
    """Validation commands."""


@validate.command("repo")
@click.option("--repo-path", required=True, type=click.Path(path_type=str))
@click.pass_context
def validate_repo_cmd(ctx: click.Context, repo_path: str) -> None:
    json_output = _json_mode(ctx)
    rules = _get_rules(ctx)
    rules_config = ctx.obj.get("rules_config")
    try:
        result = validate_repo(repo_path, rules=rules, rules_config_path=rules_config)
        payload = build_envelope(
            ok=result["ok"],
            command="validate repo",
            payload={k: v for k, v in result.items() if k not in ("ok",)},
        )
        if not result["ok"] and "error_code" in result:
            payload["error_code"] = result["error_code"]
        emit(payload, as_json=json_output)
    except Exception as exc:
        _handle_exception(exc, "validate repo", json_output)


@validate.command("scene-style")
@click.option("--scene-file", required=True, type=click.Path(path_type=str))
@click.pass_context
def validate_scene_style_cmd(ctx: click.Context, scene_file: str) -> None:
    json_output = _json_mode(ctx)
    rules = _get_rules(ctx)
    try:
        result = validate_scene_style(scene_file, rules=rules)
        payload = build_envelope(
            ok=result["ok"],
            command="validate scene-style",
            payload={k: v for k, v in result.items() if k not in ("ok",)},
        )
        if not result["ok"]:
            payload["error_code"] = "POLICY_VIOLATION"
        emit(payload, as_json=json_output)
    except Exception as exc:
        _handle_exception(exc, "validate scene-style", json_output)


@validate.command("scene-layout")
@click.option("--scene-file", required=True, type=click.Path(path_type=str))
@click.pass_context
def validate_scene_layout_cmd(ctx: click.Context, scene_file: str) -> None:
    json_output = _json_mode(ctx)
    rules = _get_rules(ctx)
    try:
        result = validate_scene_layout(scene_file, rules=rules)
        payload = build_envelope(
            ok=result["ok"],
            command="validate scene-layout",
            payload={k: v for k, v in result.items() if k not in ("ok",)},
        )
        if not result["ok"]:
            payload["error_code"] = "POLICY_VIOLATION"
        emit(payload, as_json=json_output)
    except Exception as exc:
        _handle_exception(exc, "validate scene-layout", json_output)


if __name__ == "__main__":
    main()
