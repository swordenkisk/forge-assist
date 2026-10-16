"""Command-line entry point for Forge Assist."""

from __future__ import annotations

import argparse
import difflib
import sys
from pathlib import Path

from forge_assist.api import request_file_plan
from forge_assist.config import load_config
from forge_assist.patch import parse_file_plan
from forge_assist.workspace import apply_changes, collect_context, validate_target


def _show_diff(root: Path, changes: list[dict[str, str]]) -> None:
    for change in changes:
        relative = change["path"]
        target = validate_target(root, relative)

        if target.exists():
            try:
                old_text = target.read_text(encoding="utf-8").splitlines(
                    keepends=True
                )
            except UnicodeDecodeError as exc:
                raise ValueError(
                    f"Refusing to replace a non-UTF-8 file: {relative}"
                ) from exc
            label = relative
        else:
            old_text = []
            label = "/dev/null"

        new_text = change["content"].splitlines(keepends=True)
        if change["content"] and not change["content"].endswith("\n"):
            new_text[-1] += "\n"

        print(f"\n--- {label}")
        print(f"+++ {relative}")
        diff = difflib.unified_diff(
            old_text,
            new_text,
            fromfile=label,
            tofile=relative,
        )
        sys.stdout.writelines(diff)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Ask an AI model to propose project file changes."
    )
    parser.add_argument(
        "prompt",
        nargs="+",
        help="Describe the coding task.",
    )
    parser.add_argument(
        "--workspace",
        default=".",
        help="Project directory to inspect and modify (default: current directory).",
    )
    parser.add_argument(
        "--max-context-chars",
        type=int,
        default=100_000,
        help="Maximum characters of project context sent to the AI.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=90,
        help="Request timeout in seconds.",
    )
    args = parser.parse_args()

    try:
        root = Path(args.workspace).resolve()
        if not root.is_dir():
            raise ValueError(f"Workspace is not a directory: {root}")
        if args.max_context_chars < 1:
            raise ValueError("--max-context-chars must be greater than zero.")
        if args.timeout < 1:
            raise ValueError("--timeout must be greater than zero.")

        config = load_config(root)
        context = collect_context(root, args.max_context_chars)
        model_response = request_file_plan(
            config=config,
            task=" ".join(args.prompt),
            context=context,
            timeout=args.timeout,
        )
        summary, changes = parse_file_plan(model_response)

        print(f"\nPlan: {summary}")
        _show_diff(root, changes)

        confirmation = input(
            "\nType APPLY to write these files, or press Enter to cancel: "
        )
        if confirmation != "APPLY":
            print("Cancelled; no files were written.")
            return 0

        written = apply_changes(root, changes)
        print(f"\nUpdated {len(written)} file(s):")
        for relative in written:
            print(f"  {relative}")
        return 0

    except (ValueError, OSError, RuntimeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nCancelled.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
