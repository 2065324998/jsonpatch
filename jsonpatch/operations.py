"""Individual JSON Patch (RFC 6902) operation implementations.

Each operation function takes a document and an operation dict,
applies the operation in-place, and returns the modified document.
"""

import copy

from .pointer import JsonPointer
from .exceptions import JsonPatchError, JsonPatchTestError, JsonPointerError


def apply_operation(doc, op):
    """Apply a single JSON Patch operation to a document.

    Args:
        doc: The target JSON document (modified in place).
        op: A JSON Patch operation dict with at minimum an "op" key.

    Returns:
        The modified document.

    Raises:
        JsonPatchError: If the operation is invalid or cannot be applied.
    """
    op_type = op.get("op")

    if not op_type:
        raise JsonPatchError("Operation missing 'op' field")

    handlers = {
        "add": _apply_add,
        "remove": _apply_remove,
        "replace": _apply_replace,
        "move": _apply_move,
        "copy": _apply_copy,
        "test": _apply_test,
    }

    handler = handlers.get(op_type)
    if not handler:
        raise JsonPatchError(f"Unknown operation type: {op_type!r}")

    return handler(doc, op)


def _apply_add(doc, op):
    """Apply an 'add' operation.

    Per RFC 6902: adds a value to the target location. If the target
    location specifies an object member, the member is added or replaced.
    If it specifies an array index, the value is inserted before that index.
    The '-' token appends to an array.
    """
    path = op.get("path")
    value = op.get("value")

    if path is None:
        raise JsonPatchError("'add' operation missing 'path'")

    ptr = JsonPointer(path)

    if not ptr.parts:
        # Replace the entire document
        return copy.deepcopy(value)

    parent, token = ptr.resolve_parent(doc)

    if isinstance(parent, dict):
        parent[token] = copy.deepcopy(value)
    elif isinstance(parent, list):
        if token == "-":
            parent.append(copy.deepcopy(value))
        else:
            try:
                idx = int(token)
            except ValueError:
                raise JsonPatchError(f"Invalid array index: {token!r}")
            if idx < 0 or idx > len(parent):
                raise JsonPatchError(
                    f"Array index {idx} out of range for add "
                    f"(length {len(parent)})"
                )
            parent.insert(idx, copy.deepcopy(value))
    else:
        raise JsonPatchError(
            f"Cannot add to {type(parent).__name__}"
        )

    return doc


def _apply_remove(doc, op):
    """Apply a 'remove' operation.

    Per RFC 6902: removes the value at the target location.
    The target location MUST exist.
    """
    path = op.get("path")

    if path is None:
        raise JsonPatchError("'remove' operation missing 'path'")

    ptr = JsonPointer(path)

    if not ptr.parts:
        raise JsonPatchError("Cannot remove root document")

    parent, token = ptr.resolve_parent(doc)

    if isinstance(parent, dict):
        if token not in parent:
            raise JsonPatchError(f"Cannot remove nonexistent key: {token!r}")
        del parent[token]
    elif isinstance(parent, list):
        try:
            idx = int(token)
        except ValueError:
            raise JsonPatchError(f"Invalid array index: {token!r}")
        if idx < 0 or idx >= len(parent):
            raise JsonPatchError(
                f"Array index {idx} out of range for remove "
                f"(length {len(parent)})"
            )
        del parent[idx]
    else:
        raise JsonPatchError(
            f"Cannot remove from {type(parent).__name__}"
        )

    return doc


def _apply_replace(doc, op):
    """Apply a 'replace' operation.

    Per RFC 6902: replaces the value at the target location with a new value.
    The target location MUST exist.
    """
    path = op.get("path")
    value = op.get("value")

    if path is None:
        raise JsonPatchError("'replace' operation missing 'path'")

    ptr = JsonPointer(path)

    if not ptr.parts:
        return copy.deepcopy(value)

    parent, token = ptr.resolve_parent(doc)

    if isinstance(parent, dict):
        if token not in parent:
            raise JsonPatchError(
                f"Cannot replace nonexistent key: {token!r}"
            )
        parent[token] = copy.deepcopy(value)
    elif isinstance(parent, list):
        try:
            idx = int(token)
        except ValueError:
            raise JsonPatchError(f"Invalid array index: {token!r}")
        if idx < 0 or idx >= len(parent):
            raise JsonPatchError(
                f"Array index {idx} out of range for replace "
                f"(length {len(parent)})"
            )
        parent[idx] = copy.deepcopy(value)
    else:
        raise JsonPatchError(
            f"Cannot replace in {type(parent).__name__}"
        )

    return doc


def _apply_move(doc, op):
    """Apply a 'move' operation.

    Per RFC 6902: removes the value at the 'from' location and adds it
    to the 'path' location. Functionally identical to a remove+add.
    """
    from_path = op.get("from")
    to_path = op.get("path")

    if from_path is None:
        raise JsonPatchError("'move' operation missing 'from'")
    if to_path is None:
        raise JsonPatchError("'move' operation missing 'path'")

    from_ptr = JsonPointer(from_path)

    # Get the value and remove from source
    parent, token = from_ptr.resolve_parent(doc)

    if isinstance(parent, dict):
        value = parent.pop(token, None)
    elif isinstance(parent, list):
        try:
            idx = int(token)
        except ValueError:
            raise JsonPatchError(f"Invalid array index: {token!r}")
        if idx < 0 or idx >= len(parent):
            value = None
        else:
            value = parent.pop(idx)
    else:
        value = None

    # Add at destination
    _apply_add(doc, {"op": "add", "path": to_path, "value": value})

    return doc


def _apply_copy(doc, op):
    """Apply a 'copy' operation.

    Per RFC 6902: copies the value at the 'from' location to the
    'path' location.
    """
    from_path = op.get("from")
    to_path = op.get("path")

    if from_path is None:
        raise JsonPatchError("'copy' operation missing 'from'")
    if to_path is None:
        raise JsonPatchError("'copy' operation missing 'path'")

    from_ptr = JsonPointer(from_path)

    try:
        value = from_ptr.resolve(doc)
    except JsonPointerError as e:
        raise JsonPatchError(f"Copy source not found: {e}")

    _apply_add(doc, {"op": "add", "path": to_path, "value": value})

    return doc


def _apply_test(doc, op):
    """Apply a 'test' operation.

    Per RFC 6902: tests that a value at the target location is equal to
    a specified value. Raises JsonPatchTestError if not equal.
    """
    path = op.get("path")
    expected = op.get("value")

    if path is None:
        raise JsonPatchError("'test' operation missing 'path'")

    ptr = JsonPointer(path)

    try:
        actual = ptr.resolve(doc)
    except JsonPointerError as e:
        raise JsonPatchTestError(
            f"Test target not found: {e}"
        )

    if actual != expected:
        raise JsonPatchTestError(
            f"Test failed: expected {expected!r}, got {actual!r}"
        )

    return doc
