import json
import xxhash
from dataclasses import dataclass
from typing import List, Optional, Tuple, Union

HASH_MOD = 36 * 36 * 36 * 36
RADIX = 36

def to_base36(n: int) -> str:
    chars = []
    for _ in range(4):
        rem = n % RADIX
        if rem < 10:
            chars.append(chr(ord('0') + rem))
        else:
            chars.append(chr(ord('a') + rem - 10))
        n //= RADIX
    return "".join(reversed(chars))

def compute_line_hash(line: str) -> str:
    normalized = "".join(line.split())
    # Rust XxHash64::with_seed(0)
    hasher = xxhash.xxh64(seed=0)
    hasher.update(normalized.encode('utf-8'))
    hash_val = hasher.intdigest() % HASH_MOD
    return to_base36(hash_val)

def parse_anchor(anchor: str) -> Optional[Tuple[int, str]]:
    parts = anchor.split(':', 1)
    if len(parts) != 2:
        return None
    try:
        line = int(parts[0])
        hash_val = parts[1]
        return line, hash_val
    except ValueError:
        return None

@dataclass
class SetLine:
    anchor: str
    new_text: str

@dataclass
class ReplaceLines:
    start_anchor: str
    end_anchor: str
    new_text: str

@dataclass
class InsertAfter:
    anchor: str
    text: str

@dataclass
class Replace:
    old_text: str
    new_text: str
    all: bool = False

EditOp = Union[SetLine, ReplaceLines, InsertAfter, Replace]

def parse_edits(edits_json: str) -> List[EditOp]:
    try:
        raw_edits = json.loads(edits_json)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse edits: {e}")

    ops: List[EditOp] = []
    for item in raw_edits:
        # Handle both flat and nested formats as in Rust
        if "type" in item:
            etype = item["type"]
            if etype == "set_line":
                ops.append(SetLine(anchor=item["anchor"], new_text=item["new_text"]))
            elif etype == "replace_lines":
                ops.append(ReplaceLines(start_anchor=item["start_anchor"], end_anchor=item["end_anchor"], new_text=item["new_text"]))
            elif etype == "insert_after":
                ops.append(InsertAfter(anchor=item["anchor"], text=item["text"]))
            elif etype == "replace":
                ops.append(Replace(old_text=item["old_text"], new_text=item["new_text"], all=item.get("all", False)))
        # Handle nested format
        elif "set_line" in item:
            sl = item["set_line"]
            ops.append(SetLine(anchor=sl["anchor"], new_text=sl["new_text"]))
        elif "replace_lines" in item:
            rl = item["replace_lines"]
            ops.append(ReplaceLines(start_anchor=rl["start_anchor"], end_anchor=rl["end_anchor"], new_text=rl["new_text"]))
        elif "insert_after" in item:
            ia = item["insert_after"]
            ops.append(InsertAfter(anchor=ia["anchor"], text=ia["text"]))
        elif "replace" in item:
            r = item["replace"]
            ops.append(Replace(old_text=r["old_text"], new_text=r["new_text"], all=r.get("all", False)))

    return ops

def apply_edits(content: str, edits_json: str) -> str:
    lines = content.splitlines(keepends=False)

    ops = parse_edits(edits_json)

    # First pass: validate hashes
    for op in ops:
        if isinstance(op, SetLine):
            res = parse_anchor(op.anchor)
            if res:
                line, hash_val = res
                if line == 0 or line > len(lines):
                    raise ValueError(f"Line {line} does not exist")
                expected = compute_line_hash(lines[line - 1])
                if hash_val != expected:
                    raise ValueError(f"Hash mismatch at line {line}: expected {expected}, got {hash_val}")
        elif isinstance(op, ReplaceLines):
            start_res = parse_anchor(op.start_anchor)
            end_res = parse_anchor(op.end_anchor)
            if start_res and end_res:
                start, start_hash = start_res
                end, end_hash = end_res
                if start == 0 or end == 0 or start > len(lines) or end > len(lines) or start > end:
                    raise ValueError("Line number out of range")
                expected_start = compute_line_hash(lines[start - 1])
                expected_end = compute_line_hash(lines[end - 1])
                if start_hash != expected_start or end_hash != expected_end:
                    raise ValueError("Hash mismatch in range")
        elif isinstance(op, InsertAfter):
            res = parse_anchor(op.anchor)
            if res:
                line, hash_val = res
                if line == 0 or line > len(lines):
                    raise ValueError(f"Line {line} does not exist")
                expected = compute_line_hash(lines[line - 1])
                if hash_val != expected:
                    raise ValueError(f"Hash mismatch at line {line}")

    # Separate anchor ops and replace ops
    anchor_ops = [op for op in ops if not isinstance(op, Replace)]
    replace_ops = [op for op in ops if isinstance(op, Replace)]

    # Sort anchor ops by line number descending
    def get_line(op):
        if isinstance(op, SetLine):
            res = parse_anchor(op.anchor)
            return res[0] if res else 0
        elif isinstance(op, ReplaceLines):
            res = parse_anchor(op.start_anchor)
            return res[0] if res else 0
        elif isinstance(op, InsertAfter):
            res = parse_anchor(op.anchor)
            return res[0] if res else 0
        return 0

    anchor_ops.sort(key=get_line, reverse=True)

    # Apply anchor ops
    for op in anchor_ops:
        if isinstance(op, SetLine):
            res = parse_anchor(op.anchor)
            if res:
                line, _ = res
                idx = line - 1
                new_lines = op.new_text.splitlines() if op.new_text else []
                lines[idx:idx+1] = new_lines
        elif isinstance(op, ReplaceLines):
            start_res = parse_anchor(op.start_anchor)
            end_res = parse_anchor(op.end_anchor)
            if start_res and end_res:
                start, _ = start_res
                end, _ = end_res
                new_lines = op.new_text.splitlines() if op.new_text else []
                lines[start-1:end] = new_lines
        elif isinstance(op, InsertAfter):
            res = parse_anchor(op.anchor)
            if res:
                line, _ = res
                idx = line
                new_lines = op.text.splitlines() if op.text else []
                lines[idx:idx] = new_lines

    # Apply replace ops
    for op in replace_ops:
        if isinstance(op, Replace):
            if op.all:
                lines = [l.replace(op.old_text, op.new_text) for l in lines]
            else:
                content_str = "\n".join(lines)
                pos = content_str.find(op.old_text)
                if pos != -1:
                    new_content = content_str[:pos] + op.new_text + content_str[pos + len(op.old_text):]
                    lines = new_content.splitlines()
                else:
                    raise ValueError(f"Could not find: {op.old_text}")

    return "\n".join(lines)
