import pytest
from hashline_tools.core import compute_line_hash, parse_anchor, apply_edits

def test_compute_line_hash_determinism():
    hash1 = compute_line_hash("hello world")
    hash2 = compute_line_hash("hello world")
    assert hash1 == hash2

def test_compute_line_hash_different_content():
    hash1 = compute_line_hash("hello world")
    hash2 = compute_line_hash("hello there")
    assert hash1 != hash2

def test_compute_line_hash_whitespace_normalization():
    hash1 = compute_line_hash("hello   world")
    hash2 = compute_line_hash("hello world")
    assert hash1 == hash2

def test_parse_anchor_valid():
    result = parse_anchor("42:ab12")
    assert result == (42, "ab12")

def test_parse_anchor_invalid():
    assert parse_anchor("42") is None
    assert parse_anchor("ab:cd") is None
    assert parse_anchor(":ab12") is None

def test_apply_edits_replace_lines():
    content = "line 1\nline 2\nline 3"
    lines = content.splitlines()
    hash2 = compute_line_hash(lines[1])

    edits = f'[{{"type":"replace_lines","start_anchor":"2:{hash2}","end_anchor":"2:{hash2}","new_text":"replaced line"}}]'

    new_content = apply_edits(content, edits)
    assert "replaced line" in new_content
    assert "line 2" not in new_content
    assert "line 1" in new_content
    assert "line 3" in new_content

def test_apply_edits_hash_mismatch():
    content = "line 1\nline 2"
    edits = '[{"type":"set_line","anchor":"2:zzzz","new_text":"test"}]'

    with pytest.raises(ValueError, match="Hash mismatch"):
        apply_edits(content, edits)

def test_apply_edits_replace_fuzzy():
    content = "line 1\nline 2\nline 3"
    edits = '[{"type":"replace","old_text":"line 2","new_text":"modified","all":false}]'

    new_content = apply_edits(content, edits)
    assert "modified" in new_content
