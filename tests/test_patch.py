"""Tests for full patch application and validation."""

import pytest

from jsonpatch import apply_patch, validate_patch
from jsonpatch.exceptions import JsonPatchError


class TestPatch:
    def test_apply_empty_patch(self):
        """Empty patch returns an identical document."""
        doc = {"a": 1, "b": [2, 3]}
        result = apply_patch(doc, [])
        assert result == {"a": 1, "b": [2, 3]}

    def test_apply_multiple_operations(self):
        """Multiple operations are applied sequentially."""
        doc = {"a": 1}
        patch = [
            {"op": "add", "path": "/b", "value": 2},
            {"op": "remove", "path": "/a"},
        ]
        result = apply_patch(doc, patch)
        assert result == {"b": 2}

    def test_apply_preserves_original(self):
        """apply_patch does not modify the original document by default."""
        doc = {"a": 1}
        patch = [{"op": "replace", "path": "/a", "value": 99}]
        result = apply_patch(doc, patch)
        assert result == {"a": 99}
        assert doc == {"a": 1}

    def test_validate_valid_patch(self):
        """Valid patch produces no errors."""
        patch = [
            {"op": "add", "path": "/a", "value": 1},
            {"op": "remove", "path": "/b"},
            {"op": "move", "from": "/c", "path": "/d"},
        ]
        assert validate_patch(patch) == []

    def test_validate_missing_op(self):
        """Missing 'op' field is detected."""
        patch = [{"path": "/a", "value": 1}]
        errors = validate_patch(patch)
        assert len(errors) > 0
