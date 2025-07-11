import json
from pathlib import Path
from typing import Any


def load_openapi_spec(spec_location: str) -> dict[str, Any]:
    """Load the OpenAPI spec from a local file path."""
    path = Path(spec_location)
    if not path.is_file():
        msg = f"OpenAPI spec file does not exist: {spec_location}"
        raise FileNotFoundError(msg)

    with path.open("r", encoding="utf-8") as f:
        return json.load(f)
