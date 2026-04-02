# hashline-tools

A Python CLI tool for editing files using hash-anchored line references. This tool is designed to provide safe, verifiable file edits by ensuring that the context (line content) matches a hash before applying changes.

## Features

-   **Hash-Based Anchors**: Each line is identified by a line number and a hash of its content (ignoring whitespace).
-   **Safe Edits**: Modifications are only applied if the target line's hash matches the expected value, preventing edits on stale file versions.
-   **Operations**:
    -   `read`: Read a file with line numbers and hashes.
    -   `edit`: Apply a set of JSON-encoded edit operations (`set_line`, `replace_lines`, `insert_after`, `replace`).

## Installation

This project is managed with `uv`.

```bash
# Install dependencies
uv sync
```

## Usage

You can run the tool directly using `uv run`.

### Reading a File

Read a file to get line numbers and their corresponding hashes:

```bash
uv run python -m hashline_tools.cli read <file_path> [--offset N] [--limit N]
```

Output format:
```
<file>
1:hash1|Line content 1
2:hash2|Line content 2
...
</file>
```

### Editing a File

Apply edits using a JSON string:

```bash
uv run python -m hashline_tools.cli edit <file_path> --edits '[...]'
```

#### Edit Operations

1.  **Set Line**: Replace a specific line.
    ```json
    {
      "type": "set_line",
      "anchor": "LINE_NUM:HASH",
      "new_text": "New content"
    }
    ```

2.  **Replace Lines**: Replace a range of lines.
    ```json
    {
      "type": "replace_lines",
      "start_anchor": "START_LINE:HASH",
      "end_anchor": "END_LINE:HASH",
      "new_text": "New content\nacross multiple lines"
    }
    ```

3.  **Insert After**: Insert text after a specific line.
    ```json
    {
      "type": "insert_after",
      "anchor": "LINE_NUM:HASH",
      "text": "Inserted content"
    }
    ```

4.  **Replace (Text)**: Find and replace text within the file.
    ```json
    {
      "type": "replace",
      "old_text": "foo",
      "new_text": "bar",
      "all": false
    }
    ```

## Development

Run tests using `pytest`:

```bash
uv run pytest
```
