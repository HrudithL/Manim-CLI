import json
from typing import Any

import click


def emit(payload: Any, as_json: bool) -> None:
    if as_json:
        click.echo(json.dumps(payload, indent=2, sort_keys=True))
        return
    if isinstance(payload, (dict, list)):
        click.echo(json.dumps(payload, indent=2, sort_keys=True))
        return
    click.echo(str(payload))
