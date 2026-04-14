from __future__ import annotations

import shlex
from importlib.metadata import PackageNotFoundError, version as pkg_version

import click

from manim_cli.manim._meta import MANIM_CE_VERIFIED_VERSION
from manim_cli.manim.core.analyze import analyze_scene_file
from manim_cli.manim.core.project import init_project
from manim_cli.manim.core.render import run_render
from manim_cli.manim.core.scene_index import discover_scenes
from manim_cli.manim.core.validate import validate_repo
from manim_cli.manim.utils.output import emit


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


@click.group(context_settings=CONTEXT_SETTINGS, invoke_without_command=True)
@click.version_option(
    _cli_version_message(),
    "--version",
    prog_name="manim-cli",
)
@click.option("--json-output", "--json", is_flag=True, default=False, help="Emit JSON output.")
@click.pass_context
def main(ctx: click.Context, json_output: bool) -> None:
    """Manim CLI harness."""
    ctx.ensure_object(dict)
    ctx.obj["json_output"] = json_output
    if ctx.invoked_subcommand is None:
        _run_repl(json_output=json_output)


def _run_repl(json_output: bool) -> None:
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
            main.main(args=args, prog_name="manim-cli", standalone_mode=False, obj={"json_output": json_output})
        except SystemExit:
            continue
        except Exception as exc:  # pragma: no cover - REPL safety net
            emit({"ok": False, "error": str(exc)}, as_json=json_output)


@main.group()
def project() -> None:
    """Project commands."""


@project.command("init")
@click.option("--target-dir", required=True, type=click.Path(path_type=str))
@click.option("--scene-name", default="HelloScene", show_default=True)
@click.pass_context
def project_init(ctx: click.Context, target_dir: str, scene_name: str) -> None:
    emit(init_project(target_dir=target_dir, scene_name=scene_name), as_json=ctx.obj["json_output"])


@main.group()
def scene() -> None:
    """Scene discovery commands."""


@scene.command("list")
@click.option("--repo-path", required=True, type=click.Path(exists=True, path_type=str))
@click.pass_context
def scene_list(ctx: click.Context, repo_path: str) -> None:
    scenes = discover_scenes(repo_path)
    payload = {
        "ok": True,
        "count": len(scenes),
        "scenes": [s.__dict__ for s in scenes],
    }
    emit(payload, as_json=ctx.obj["json_output"])


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
    payload = run_render(
        scene_file=scene_file,
        scene_name=scene_name,
        quality=quality,
        renderer=renderer,
        output_dir=output_dir,
        dry_run=dry_run,
    )
    emit(payload, as_json=ctx.obj["json_output"])


@main.group()
def analyze() -> None:
    """AST analysis commands."""


@analyze.command("scene-file")
@click.option("--scene-file", required=True, type=click.Path(exists=True, path_type=str))
@click.pass_context
def analyze_scene_file_cmd(ctx: click.Context, scene_file: str) -> None:
    emit(analyze_scene_file(scene_file), as_json=ctx.obj["json_output"])


@main.group()
def validate() -> None:
    """Validation commands."""


@validate.command("repo")
@click.option("--repo-path", required=True, type=click.Path(path_type=str))
@click.pass_context
def validate_repo_cmd(ctx: click.Context, repo_path: str) -> None:
    emit(validate_repo(repo_path), as_json=ctx.obj["json_output"])


if __name__ == "__main__":
    main()
