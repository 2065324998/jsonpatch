"""Generate JSON Patch (RFC 6902) diffs between two JSON documents.

Given a source and destination document, produces a list of patch
operations that transform the source into the destination.
"""

from typing import Any


def diff(src: Any, dst: Any, path: str = "") -> list[dict]:
    """Generate a JSON Patch diff between two values.

    Args:
        src: The source document (or sub-document).
        dst: The destination document (or sub-document).
        path: The current JSON Pointer path prefix (used in recursion).

    Returns:
        A list of JSON Patch operation dicts.
    """
    if _values_equal(src, dst):
        return []

    # Different types: full replace
    if type(src) is not type(dst):
        return [{"op": "replace", "path": path or "/", "value": dst}]

    if isinstance(src, dict):
        return _diff_dicts(src, dst, path)
    elif isinstance(src, list):
        return _diff_lists(src, dst, path)
    else:
        # Scalar values differ
        return [{"op": "replace", "path": path, "value": dst}]


def _diff_dicts(src: dict, dst: dict, path: str) -> list[dict]:
    """Generate patch operations for two dicts.

    Detects additions, removals, and in-place modifications.
    When a value is removed from one key and an identical value
    appears at a new key, generates a 'move' operation for efficiency.
    """
    ops = []

    src_keys = set(src.keys())
    dst_keys = set(dst.keys())

    removed_keys = src_keys - dst_keys
    added_keys = dst_keys - src_keys
    common_keys = src_keys & dst_keys

    # Check for values that moved between keys
    moves = _detect_moves(src, dst, removed_keys, added_keys)

    moved_from = {m[0] for m in moves}
    moved_to = {m[1] for m in moves}

    # Generate move operations
    for from_key, to_key, _ in moves:
        ops.append({
            "op": "move",
            "from": f"{path}/{from_key}",
            "path": f"{path}/{to_key}",
        })

    # Remove keys (excluding those involved in moves)
    for key in sorted(removed_keys - moved_from):
        ops.append({"op": "remove", "path": f"{path}/{key}"})

    # Recurse into modified keys
    for key in sorted(common_keys):
        if src[key] != dst[key]:
            ops.extend(diff(src[key], dst[key], f"{path}/{key}"))

    # Add new keys (excluding those involved in moves)
    for key in sorted(added_keys - moved_to):
        ops.append({
            "op": "add",
            "path": f"{path}/{key}",
            "value": dst[key],
        })

    return ops


def _diff_lists(src: list, dst: list, path: str) -> list[dict]:
    """Generate patch operations for two lists.

    Uses element-by-element comparison. For elements present in both
    lists (up to the shorter length), generates recursive diffs.
    Extra elements are removed or added as needed.
    """
    ops = []

    min_len = min(len(src), len(dst))

    # Compare common elements
    for i in range(min_len):
        ops.extend(diff(src[i], dst[i], f"{path}/{i}"))

    # Remove extra elements from source (in reverse order to maintain indices)
    for i in range(len(src) - 1, min_len - 1, -1):
        ops.append({"op": "remove", "path": f"{path}/{i}"})

    # Add extra elements to reach destination
    for i in range(min_len, len(dst)):
        ops.append({
            "op": "add",
            "path": f"{path}/{i}",
            "value": dst[i],
        })

    return ops


def _detect_moves(src, dst, removed_keys, added_keys):
    """Detect values that moved from one key to another.

    When the same value exists under a removed key and an added key,
    we can use a 'move' operation instead of remove + add.

    Args:
        src: Source dict.
        dst: Destination dict.
        removed_keys: Keys present in src but not dst.
        added_keys: Keys present in dst but not src.

    Returns:
        List of (from_key, to_key, value) tuples.
    """
    moves = []
    used_removed = set()
    used_added = set()

    for rem_key in sorted(removed_keys):
        if rem_key in used_removed:
            continue
        for add_key in sorted(added_keys):
            if add_key in used_added:
                continue
            if _values_equal(src[rem_key], dst[add_key]):
                moves.append((rem_key, add_key, dst[add_key]))
                used_removed.add(rem_key)
                used_added.add(add_key)
                break

    return moves


def _values_equal(a, b):
    """Deep equality check for JSON values."""
    if type(a) is not type(b):
        return False
    if isinstance(a, dict):
        if set(a.keys()) != set(b.keys()):
            return False
        return all(_values_equal(a[k], b[k]) for k in a)
    if isinstance(a, list):
        if len(a) != len(b):
            return False
        return all(_values_equal(x, y) for x, y in zip(a, b))
    return a == b
