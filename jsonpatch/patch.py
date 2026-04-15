"""Apply a complete JSON Patch (RFC 6902) to a document.

A JSON Patch is an ordered list of operations. Operations are applied
sequentially; if any operation fails, the patch is aborted and an
exception is raised.
"""

import copy
from typing import Any

from .operations import apply_operation
from .exceptions import JsonPatchError


def apply_patch(doc: Any, patch: list[dict], in_place: bool = False) -> Any:
    """Apply a JSON Patch to a document.

    Args:
        doc: The target JSON document.
        patch: A list of JSON Patch operation dicts.
        in_place: If True, modify the document in place. If False (default),
            work on a deep copy to preserve the original.

    Returns:
        The patched document.

    Raises:
        JsonPatchError: If any operation fails.
    """
    if not isinstance(patch, list):
        raise JsonPatchError("Patch must be a list of operations")

    result = doc if in_place else copy.deepcopy(doc)

    for i, op in enumerate(patch):
        if not isinstance(op, dict):
            raise JsonPatchError(
                f"Operation {i} is not a dict: {type(op).__name__}"
            )
        try:
            result = apply_operation(result, op)
        except JsonPatchError:
            raise
        except Exception as e:
            raise JsonPatchError(
                f"Operation {i} ({op.get('op', '?')}) failed: {e}"
            )

    return result


def validate_patch(patch: list[dict]) -> list[str]:
    """Validate a JSON Patch for structural correctness.

    Checks that each operation has the required fields per RFC 6902.
    Does NOT check that the operations can be applied to any particular
    document.

    Args:
        patch: A list of JSON Patch operation dicts.

    Returns:
        A list of error messages (empty if valid).
    """
    if not isinstance(patch, list):
        return ["Patch must be a list of operations"]

    errors = []

    required_fields = {
        "add": ["path", "value"],
        "remove": ["path"],
        "replace": ["path", "value"],
        "move": ["from", "path"],
        "copy": ["from", "path"],
        "test": ["path", "value"],
    }

    for i, op in enumerate(patch):
        if not isinstance(op, dict):
            errors.append(f"Operation {i}: not a dict")
            continue

        op_type = op.get("op")
        if not op_type:
            errors.append(f"Operation {i}: missing 'op' field")
            continue

        if op_type not in required_fields:
            errors.append(f"Operation {i}: unknown type {op_type!r}")
            continue

        for field in required_fields[op_type]:
            if field not in op:
                errors.append(
                    f"Operation {i} ({op_type}): missing '{field}'"
                )

    return errors
