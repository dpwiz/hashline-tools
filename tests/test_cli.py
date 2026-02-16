import pytest
from click.testing import CliRunner
from hashline_tools.cli import main
from hashline_tools.core import compute_line_hash

def test_cli_read():
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open('test.txt', 'w') as f:
            f.write("line 1\nline 2\nline 3\n")

        result = runner.invoke(main, ['read', 'test.txt'])
        assert result.exit_code == 0
        assert "1:" in result.output
        assert "|line 1" in result.output
        assert "2:" in result.output
        assert "|line 2" in result.output
        assert "(End of file" in result.output

def test_cli_read_offset():
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open('test.txt', 'w') as f:
            f.write("line 1\nline 2\nline 3\n")

        result = runner.invoke(main, ['read', 'test.txt', '--offset', '1'])
        assert result.exit_code == 0
        assert "|line 1" not in result.output
        assert "2:" in result.output
        assert "|line 2" in result.output

def test_cli_edit_replace_lines():
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open('test.txt', 'w') as f:
            f.write("line 1\nline 2\nline 3\n")

        # Calculate hash for line 2
        hash2 = compute_line_hash("line 2")
        edits = f'[{{"type":"replace_lines","start_anchor":"2:{hash2}","end_anchor":"2:{hash2}","new_text":"replaced line"}}]'

        result = runner.invoke(main, ['edit', 'test.txt', '--edits', edits])
        assert result.exit_code == 0
        assert "Edit applied successfully" in result.output
        assert "-line 2" in result.output
        assert "+replaced line" in result.output

        with open('test.txt', 'r') as f:
            new_content = f.read()
            assert "replaced line" in new_content
            assert "line 2\n" not in new_content

def test_cli_edit_hash_mismatch():
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open('test.txt', 'w') as f:
            f.write("line 1\nline 2\n")

        edits = '[{"type":"set_line","anchor":"2:zzzz","new_text":"test"}]'
        result = runner.invoke(main, ['edit', 'test.txt', '--edits', edits])
        assert result.exit_code == 1
        assert "Hash mismatch" in result.output
