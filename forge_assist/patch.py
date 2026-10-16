"""Parse and validate the AI's proposed file plan."""

from __future__ import annotations

import json
import re


def parse_file_plan(text: str) -> tuple[str, list[dict[str, str]]]:
    """Parse a JSON file plan, accepting an optional outer JSON code fence."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, count=1)
        cleaned = re.sub(r"\s*```\$", "", cleaned, count=1).strip()

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ValueError(f"AI response was not valid JSON: {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError("AI response must be a JSON object.")

    summary = data.get("summary")
    files = data.get("files")
    if not isinstance(summary, str) or not isinstance(files, list):
        raise ValueError("AI response must contain a string summary and a files list.")
    if not files:
        raise ValueError("AI response proposed no files.")

    validated: list[dict[str, str]] = []
    seen\_paths: set[str] = set()

    for index, item in enumerate(files):
        if not isinstance(item, dict):
            raise ValueError(f"File entry {index} must be a JSON object.")

        path = item.get("path")
        content = item.get("content")
        if not isinstance(path, str) or not isinstance(content, str):
            raise ValueError(
                f"File entry {index} must contain string path and content values."
            )
        if path in seen\_paths:
            raise ValueError(f"AI response contains a duplicate path: {path}")
        if len(content.encode("utf-8")) > 500\_000:
            raise ValueError(f"Proposed file is too large: {path}")

        seen\_paths.add(path)
        validated.append({"path": path, "content": content})

    return summary, validated
