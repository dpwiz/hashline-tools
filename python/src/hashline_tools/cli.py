import click
import sys
import difflib
from .core import compute_line_hash, apply_edits

@click.group()
def main():
    """Hashline tools for opencode"""
    pass

@main.command()
@click.argument('file_path', type=click.Path(exists=True))
@click.option('--offset', type=int, default=0, help='Line offset (0-based)')
@click.option('--limit', type=int, default=2000, help='Number of lines to read')
def read(file_path, offset, limit):
    """Read a file with hashline format"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        click.echo(f"Failed to read file: {e}", err=True)
        sys.exit(1)

    lines = content.splitlines(keepends=False)

    total_lines = len(lines)
    start = offset
    end = min(start + limit, total_lines)

    if start >= total_lines:
        click.echo("<file>\n(End of file - 0 lines)\n</file>")
        return

    output_lines = []
    for i in range(start, end):
        line = lines[i]
        line_num = i + 1
        hash_val = compute_line_hash(line)
        output_lines.append(f"{line_num}:{hash_val}|{line}")

    output = "\n".join(output_lines)

    if end < total_lines:
        end_msg = f"\n\n(File has more lines. Use 'offset' parameter to read beyond line {end})"
    else:
        end_msg = f"\n\n(End of file - {total_lines} total lines)"

    click.echo(f"<file>\n{output}{end_msg}\n</file>")

@main.command()
@click.argument('file_path', type=click.Path(exists=True))
@click.option('--edits', required=True, help='JSON edits')
def edit(file_path, edits):
    """Edit a file using hashline anchors"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        click.echo(f"Failed to read file: {e}", err=True)
        sys.exit(1)

    try:
        new_content = apply_edits(content, edits)
    except Exception as e:
        # Print error message and exit with error code
        # Rust format: just prints the error string.
        # But here we are in a CLI. If we want to mimic Rust's Result display:
        # Rust default `main` error display is `Error: <message>`
        # But the `cmd_edit` function returns `Result<String, String>`.
        # If it returns Err, `main` might print it.
        # But I'll use click.echo(..., err=True) for safety.
        click.echo(f"{e}", err=True)
        sys.exit(1)

    # Normalize content for comparison (handle CRLF vs LF)
    normalized_content = "\n".join(content.splitlines(keepends=False))

    if new_content == normalized_content:
        click.echo("No changes made")
        return

    # Generate diff
    # Use splitlines(keepends=True) to preserve newlines for difflib
    # But apply_edits result (new_content) doesn't have trailing newlines for each line if constructed via join("\n")
    # So we should splitlines(keepends=True) on both but manually ensure consistency

    old_lines = [l + "\n" for l in normalized_content.splitlines(keepends=False)]
    new_lines = [l + "\n" for l in new_content.splitlines(keepends=False)]

    # Check if original content was empty?
    if not normalized_content:
        old_lines = []
    if not new_content:
        new_lines = []

    diff = difflib.ndiff(old_lines, new_lines)

    diff_output = []
    for line in diff:
        if line.startswith('? '):
            continue
        marker = line[:2]
        text = line[2:]
        if marker == '- ':
            diff_output.append(f"-{text}")
        elif marker == '+ ':
            diff_output.append(f"+{text}")
        elif marker == '  ':
            diff_output.append(f" {text}")

    diff_str = "".join(diff_output)

    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
    except Exception as e:
        click.echo(f"Failed to write file: {e}", err=True)
        sys.exit(1)

    click.echo(f"Edit applied successfully.\n\n<diff>\n--- {file_path}\n+++ {file_path}\n{diff_str}\n</diff>")

if __name__ == '__main__':
    main()
