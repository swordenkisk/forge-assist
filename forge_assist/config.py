"""Load provider settings from the environment and an optional .env file."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Config:
    api_base_url: str
    api_key: str
    model: str


def _read_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}

    if not path.exists():
        return values

    for line_number, raw_line in enumerate(
        path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise ValueError(f"Invalid .env line {line_number}: expected KEY=VALUE.")

        key, value = line.split("=", maxsplit=1)
        key = key.strip()
        value = value.strip()

        if not key:
            raise ValueError(f"Invalid .env line {line_number}: empty key.")

        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]

        values[key] = value

    return values


def load_config(workspace: Path) -> Config:
    file_values = _read_env_file(workspace / ".env")

    def get_value(name: str) -> str:
        return os.environ.get(name, file_values.get(name, "")).strip()

    base_url = get_value("API_BASE_URL").rstrip("/")
    api_key = get_value("API_KEY")
    model = get_value("MODEL")

    missing = [
        name
        for name, value in (
            ("API_BASE_URL", base_url),
            ("API_KEY", api_key),
            ("MODEL", model),
        )
        if not value or value.startswith("replace-with-")
    ]
    if missing:
        raise ValueError(
            "Set these values in .env or the environment: " + ", ".join(missing)
        )

    return Config(api_base_url=base_url, api_key=api_key, model=model)
