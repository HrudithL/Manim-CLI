from manim_cli.manim.core.render import build_render_command


def test_build_render_command_contains_expected_parts() -> None:
    cmd = build_render_command(
        scene_file="scene.py",
        scene_name="MyScene",
        quality="l",
        renderer="cairo",
        output_dir="media",
    )
    assert cmd[0] == "manim"
    assert "-ql" in cmd
    assert "--renderer=cairo" in cmd
    assert "--media_dir" in cmd
    assert "scene.py" in cmd
    assert "MyScene" in cmd
