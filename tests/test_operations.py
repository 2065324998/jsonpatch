"""Tests for individual JSON Patch operations."""

import pytest

from jsonpatch import apply_operation
from jsonpatch.exceptions import JsonPatchError, JsonPatchTestError


class TestOperations:
    def test_add_to_dict(self):
        """Add a new key to a dict."""
        doc = {"a": 1}
        result = apply_operation(doc, {"op": "add", "path": "/b", "value": 2})
        assert result == {"a": 1, "b": 2}

    def test_add_to_array_insert(self):
        """Insert into the middle of an array."""
        doc = {"items": [1, 3]}
        result = apply_operation(
            doc, {"op": "add", "path": "/items/1", "value": 2}
        )
        assert result == {"items": [1, 2, 3]}

    def test_add_to_array_append(self):
        """Append to an array using the '-' token."""
        doc = {"items": [1, 2]}
        result = apply_operation(
            doc, {"op": "add", "path": "/items/-", "value": 3}
        )
        assert result == {"items": [1, 2, 3]}

    def test_remove_from_dict(self):
        """Remove a key from a dict."""
        doc = {"a": 1, "b": 2}
        result = apply_operation(doc, {"op": "remove", "path": "/a"})
        assert result == {"b": 2}

    def test_replace_in_dict(self):
        """Replace an existing dict value."""
        doc = {"a": 1}
        result = apply_operation(
            doc, {"op": "replace", "path": "/a", "value": 99}
        )
        assert result == {"a": 99}

    def test_copy_between_keys(self):
        """Copy a nested value to a new key."""
        doc = {"a": {"x": 1}}
        result = apply_operation(
            doc, {"op": "copy", "from": "/a", "path": "/b"}
        )
        assert result == {"a": {"x": 1}, "b": {"x": 1}}
        # Verify deep copy (modifying copy doesn't affect original)
        result["b"]["x"] = 999
        assert result["a"]["x"] == 1

    def test_move_dict_key(self):
        """Move a value from one key to another."""
        doc = {"a": 1, "b": 2}
        result = apply_operation(
            doc, {"op": "move", "from": "/a", "path": "/c"}
        )
        assert result == {"b": 2, "c": 1}

    def test_test_operation_passes(self):
        """Test operation succeeds when values match."""
        doc = {"a": [1, 2, 3]}
        result = apply_operation(
            doc, {"op": "test", "path": "/a", "value": [1, 2, 3]}
        )
        assert result == {"a": [1, 2, 3]}

    def test_test_operation_fails(self):
        """Test operation raises when values don't match."""
        doc = {"a": 1}
        with pytest.raises(JsonPatchTestError):
            apply_operation(doc, {"op": "test", "path": "/a", "value": 2})

    def test_unknown_op_raises(self):
        """Unknown operation type raises."""
        with pytest.raises(JsonPatchError):
            apply_operation({}, {"op": "invalid"})
