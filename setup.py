from setuptools import find_packages, setup


setup(
    name="manim-cli",
    version="0.1.0",
    description="Standalone developer CLI harness for Manim CE (see README for verified Manim CE version)",
    packages=find_packages(),
    include_package_data=True,
    install_requires=["click>=8.1.7"],
    entry_points={
        "console_scripts": [
            "manim-cli=manim_cli.manim.cli:main",
        ]
    },
)
