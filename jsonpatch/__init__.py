"""jsonpatch — JSON Patch (RFC 6902) implementation.

Provides tools for generating and applying JSON Patch documents.
Supports all six operation types: add, remove, replace, move, copy, test.

Usage:
    from jsonpatch import diff, apply_patch, JsonPointer

    patch = diff(source, target)
    result = apply_patch(source, patch)
    assert result == target
"""

from .pointer import JsonPointer
from .diff import diff
from .patch import apply_patch, validate_patch
from .operations import apply_operation
from .exceptions import (
    JsonPointerError,
    JsonPatchError,
    JsonPatchTestError,
    JsonPatchConflictError,
)

__version__ = "0.3.1"

__all__ = [
    "JsonPointer",
    "diff",
    "apply_patch",
    "validate_patch",
    "apply_operation",
    "JsonPointerError",
    "JsonPatchError",
    "JsonPatchTestError",
    "JsonPatchConflictError",
]
