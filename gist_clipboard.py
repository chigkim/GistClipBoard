#!/usr/bin/env python3
"""Use a GitHub gist named CLIPBOARD as a simple shared clipboard."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from typing import Sequence

GIST_ID_RE = re.compile(r"^([0-9a-f]{8,})\b", re.IGNORECASE)


def run_command(args: Sequence[str], stdin_text: str | None = None) -> str:
    """Run a command and return stdout, raising a useful error on failure."""
    try:
        completed = subprocess.run(
            list(args),
            input=stdin_text,
            capture_output=True,
            text=True,
            check=True,
        )
    except FileNotFoundError as exc:
        raise RuntimeError(f"Command not found: {args[0]}") from exc
    except subprocess.CalledProcessError as exc:
        message = exc.stderr.strip() or exc.stdout.strip() or str(exc)
        raise RuntimeError(message) from exc

    return completed.stdout


def announce_action(message: str) -> None:
    """Speak a short status message when supported by the local OS."""
    try:
        if sys.platform == "darwin":
            subprocess.run(["say", message], check=True)
            return

        if sys.platform.startswith("win"):
            escaped = message.replace("'", "''")
            subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-Command",
                    (
                        "Add-Type -AssemblyName System.Speech; "
                        "$speak = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
                        f"$speak.Speak('{escaped}')"
                    ),
                ],
                check=True,
            )
    except Exception:
        # Speech is best-effort and should not block clipboard sync.
        pass


def find_gist_id(keyword: str, limit: int) -> str | None:
    """Return the first gist ID matching the keyword in the list output."""
    output = run_command(
        ["gh", "gist", "list", "--filter", keyword, "--limit", str(limit)]
    )

    for line in output.splitlines():
        match = GIST_ID_RE.match(line.strip())
        if match:
            return match.group(1)

    return None


def get_gist_filename(gist_id: str) -> str:
    """Return the first filename in the gist."""
    output = run_command(["gh", "gist", "view", gist_id, "--files"])

    for line in output.splitlines():
        filename = line.strip()
        if filename:
            return filename

    raise RuntimeError(f"Gist {gist_id} does not contain any files.")


def fetch_gist_content(gist_id: str) -> str:
    """Fetch raw content for the first file in a gist."""
    filename = get_gist_filename(gist_id)
    return run_command(["gh", "gist", "view", gist_id, "--raw", "--filename", filename])


def copy_to_clipboard(text: str) -> None:
    """Copy text to the local clipboard using native OS tools when available."""
    # On Windows, tkinter's clipboard can appear to succeed but lose ownership when
    # the short-lived process exits, leaving the clipboard empty. Prefer the native
    # clipboard command there.
    if sys.platform.startswith("win"):
        subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                "Set-Clipboard -Value ([Console]::In.ReadToEnd())",
            ],
            input=text,
            text=True,
            check=True,
        )
        return

    if sys.platform == "darwin":
        subprocess.run(["pbcopy"], input=text, text=True, check=True)
        return

    try:
        import tkinter as tk

        root = tk.Tk()
        root.withdraw()
        root.clipboard_clear()
        root.clipboard_append(text)
        root.update()
        root.destroy()
        return
    except Exception:
        pass

    raise RuntimeError(
        "Could not access the clipboard with stdlib tools on this platform. "
        "Install a clipboard utility or run on Windows/macOS."
    )


def read_clipboard() -> str:
    """Read text from the local clipboard using stdlib first, shell fallback second."""
    try:
        import tkinter as tk

        root = tk.Tk()
        root.withdraw()
        text = root.clipboard_get()
        root.destroy()
        return text
    except Exception:
        pass

    if sys.platform.startswith("win"):
        completed = subprocess.run(
            ["powershell", "-NoProfile", "-Command", "Get-Clipboard -Raw"],
            capture_output=True,
            text=True,
            check=True,
        )
        return completed.stdout

    if sys.platform == "darwin":
        completed = subprocess.run(
            ["pbpaste"],
            capture_output=True,
            text=True,
            check=True,
        )
        return completed.stdout

    raise RuntimeError(
        "Could not read the clipboard with stdlib tools on this platform. "
        "Install a clipboard utility or run on Windows/macOS."
    )


def create_clipboard_gist(description: str, content: str, filename: str) -> str:
    """Create a gist from the current clipboard content when no remote gist exists."""
    return run_command(
        ["gh", "gist", "create", "-", "--desc", description, "--filename", filename],
        stdin_text=content,
    ).strip()


def sync_clipboard(description: str, limit: int, filename: str) -> int:
    gist_id = find_gist_id(description, limit)

    if gist_id:
        content = fetch_gist_content(gist_id)
        copy_to_clipboard(content)
        run_command(["gh", "gist", "delete", gist_id, "--yes"])
        print(f"Copied gist {gist_id} to the local clipboard and deleted the gist.")
        announce_action("Clipboard pulled")
        return 0

    content = read_clipboard()
    gist_ref = create_clipboard_gist(description, content, filename)
    print(f"No matching gist found. Created new gist: {gist_ref}")
    announce_action("Clipboard pushed")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Find a GitHub gist by description and copy its content to the clipboard."
    )
    parser.add_argument(
        "--description",
        default="GH_CLIPBOARD",
        help="Keyword used to find the gist. Default: GH_CLIPBOARD",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=100,
        help="Maximum number of gists to scan. Default: 100",
    )
    parser.add_argument(
        "--filename",
        default="clipboard.txt",
        help="Filename used for the gist content. Default: clipboard.txt",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        return sync_clipboard(args.description, args.limit, args.filename)
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
