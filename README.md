# Gist Clipboard

A simple tool to sync your clipboard across machines using GitHub Gists as a temporary buffer. This project provides a "push-pull" mechanism that uses the GitHub CLI (`gh`) to handle the heavy lifting.

## Features

- **Push-Pull Logic**: If a sync gist exists, it pulls the content to your local clipboard and deletes the gist. If not, it creates a new gist with your current clipboard content.
- **Cross-Platform**: Works on Windows and macOS.
- **Voice Feedback**: Uses system text-to-speech to announce when the clipboard has been "pushed" or "pulled".
- **GitHub CLI Integration**: Uses the reliable `gh` tool for secure and easy gist management.

## Prerequisites

- **[GitHub CLI](https://cli.github.com/) (gh)**: Must be installed and authenticated (`gh auth login`).

## Installation

1.  Clone this repository or download the files.
2.  Ensure you have the GitHub CLI installed and logged in.

## Usage

### Shortcuts

- **Windows**: Double-click `gist_clipboard.bat`.
- **macOS**: Double-click `gist_clipboard.command`.

Ensure the path in the file matches your local installation directory.

### Basic Command

Run the tool using the Python script:

```bash
python gist_clipboard.py
```

### Options

```text
usage: gist_clipboard.py [-h] [--description DESCRIPTION] [--limit LIMIT] [--filename FILENAME]

Find a GitHub gist by description and copy its content to the clipboard.

optional arguments:
  -h, --help            show this help message and exit
  --description DESCRIPTION
                        Keyword used to find the gist. Default: GH_CLIPBOARD
  --limit LIMIT         Maximum number of gists to scan. Default: 100
  --filename FILENAME   Filename used for the gist content. Default: clipboard.txt
```

## How it Works

1.  **Pull**: If a Gist with the description `GH_CLIPBOARD` exists, the script:
    *   Fetches the Gist's content.
    *   Copies it to your local clipboard.
    *   Deletes the Gist from GitHub.
    *   Announces "Clipboard pulled" via audio.
2.  **Push**: If no matching Gist is found:
    *   Reads your local clipboard content.
    *   Creates a new Gist with that content and description `GH_CLIPBOARD`.
    *   Announces "Clipboard pushed" via audio.

## Notes

- **Privacy**: The script creates secret gists by default via `gh gist create`. However, your data still passes through GitHub's servers. Avoid syncing highly sensitive information.
- **Cleanup**: The script automatically deletes the Gist after a successful pull to keep your Gist list clean.
