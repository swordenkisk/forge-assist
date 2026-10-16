"""Workspace context collection and guarded file updates."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path, PurePosixPath


IGNORED\_DIRECTORIES = {
    ".git",
    ".venv",
    "venv",
    "node\_modules",
    "\_\_pycache\_\_",
    ".brainforge",
    "build",
    "dist",
}
PRIVATE\_NAMES = {
    "id\_rsa",
    "id\_ed25519",
    "credentials.json",
    "secrets.json",
}
PRIVATE\_SUFFIXES = {".pem", ".key", ".p12", ".pfx"}


def _is\_private\_file(path: Path) -> bool:
    name = path.name.lower()
    return (
        name == ".env"
        or name.startswith(".env.")
        or name in PRIVATE\_NAMES
        or path.suffix.lower() in PRIVATE\_SUFFIXES
    )


def _inside\_workspace(root: Path, target: Path) -> bool:
    try:
        target.resolve(strict=False).relative\_to(root.resolve())
        return True
    except ValueError:
        return False


def validate\_target(root: Path, relative\_path: str) -> Path:
    """Validate a model-provided relative path and return its safe target."""
    if not relative\_path or "\x00" in relative\_path:
        raise ValueError("File paths must be non-empty and contain no NUL bytes.")

    portable\_path = relative\_path.replace("\\", "/")
    parsed = PurePosixPath(portable\_path)

    if parsed.is\_absolute() or ".." in parsed.parts or ":" in portable\_path:
        raise ValueError(f"Unsafe file path: {relative\_path}")
    if not parsed.parts or any(part in {".", ""} for part in parsed.parts):
        raise ValueError(f"Invalid file path: {relative\_path}")
    if any(part.lower() in {".git", ".brainforge"} for part in parsed.parts):
        raise ValueError(f"Protected directory in file path: {relative\_path}")

    target = root.joinpath(\*parsed.parts)
    if not \_inside\_workspace(root, target):
        raise ValueError(f"File path escapes the workspace: {relative\_path}")
    if \_is\_private\_file(target):
        raise ValueError(f"Refusing to write a private configuration or key file: {relative\_path}")

    return target


def collect\_context(root: Path, max\_chars: int = 100\_000) -> str:
    """Collect a bounded text snapshot while skipping common secrets and artifacts."""
    root = root.resolve()
    files: list[Path] = []

    for current, directory\_names, file\_names in os.walk(root, followlinks=False):
        directory\_names[:] = sorted(
            name
            for name in directory\_names
            if name not in IGNORED\_DIRECTORIES
            and not (Path(current) / name).is\_symlink()
        )
        for name in sorted(file\_names):
            path = Path(current) / name
            if path.is\_symlink() or _is\_private\_file(path):
                continue
            if not _inside\_workspace(root, path):
                continue
            try:
                if path.stat().st\_size > 80\_000:
                    continue
            except OSError:
                continue
            files.append(path)

    relative\_files = [path.relative\_to(root).as\_posix() for path in files]
    output = ["Project files:", *[f"- {name}" for name in relative\_files], "", "File contents:"]

    used = sum(len(line) + 1 for line in output)
    for path, relative in zip(files, relative\_files):
        try:
            content = path.read\_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue

        block = f"\n--- {relative} ---\n{content}\n"
        if used + len(block) > max\_chars:
            remaining = max\_chars - used
            if remaining > 0:
                output.append(block[:remaining])
            break

        output.append(block)
        used += len(block)

    return "\n".join(output)[:max\_chars]


def apply\_changes(root: Path, changes: list[dict[str, str]]) -> list[str]:
    """Write validated UTF-8 files using atomic replacement per file."""
    root = root.resolve()
    targets: list[tuple[str, Path, str]] = []
    seen: set[str] = set()

    for change in changes:
        relative = change["path"]
        content = change["content"]
        if relative in seen:
            raise ValueError(f"Duplicate target path: {relative}")
        seen.add(relative)

        target = validate\_target(root, relative)
        if target.exists() and not target.is\_file():
            raise ValueError(f"Target is not a regular file: {relative}")
        if target.exists():
            try:
                target.read\_bytes().decode("utf-8")
            except UnicodeDecodeError as exc:
                raise ValueError(
                    f"Refusing to replace a non-UTF-8 file: {relative}"
                ) from exc
        targets.append((relative, target, content))

    staged: list[tuple[str, Path, Path]] = []
    try:
        for relative, target, content in targets:
            target.parent.mkdir(parents=True, exist\_ok=True)
            if not _inside\_workspace(root, target):
                raise ValueError(f"File path escapes the workspace: {relative}")

            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                newline="",
                dir=target.parent,
                prefix=".forge-assist-",
                suffix=".tmp",
                delete=False,
            ) as temporary:
                temporary.write(content)
                temporary\_path = Path(temporary.name)

            staged.append((relative, target, temporary\_path))

        for _, target, temporary\_path in staged:
            os.replace(temporary\_path, target)

    finally:
        for _, _, temporary\_path in staged:
            if temporary\_path.exists():
                temporary\_path.unlink()

    return [relative for relative, _, _ in targets]
