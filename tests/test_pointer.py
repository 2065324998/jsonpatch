"""Tests for JSON Pointer (RFC 6901) resolution."""

import pytest

from jsonpatch import JsonPointer
from jsonpatch.exceptions import JsonPointerError


class TestJsonPointer:
    def test_resolve_root(self):
        """Empty pointer resolves to the whole document."""
        doc = {"a": 1, "b": 2}
        ptr = JsonPointer("")
        assert ptr.resolve(doc) == {"a": 1, "b": 2}

    def test_resolve_simple_key(self):
        """Single token resolves to a dict key."""
        doc = {"foo": "bar", "baz": 42}
        ptr = JsonPointer("/foo")
        assert ptr.resolve(doc) == "bar"

    def test_resolve_nested(self):
        """Multi-token pointer resolves through nested dicts."""
        doc = {"a": {"b": {"c": 42}}}
        ptr = JsonPointer("/a/b/c")
        assert ptr.resolve(doc) == 42

    def test_resolve_array_index(self):
        """Numeric token resolves to array index."""
        doc = {"items": [10, 20, 30]}
        ptr = JsonPointer("/items/1")
        assert ptr.resolve(doc) == 20

    def test_resolve_parent(self):
        """resolve_parent returns (parent_container, last_token)."""
        doc = {"a": {"b": 1, "c": 2}}
        ptr = JsonPointer("/a/b")
        parent, token = ptr.resolve_parent(doc)
        assert parent == {"b": 1, "c": 2}
        assert token == "b"

    def test_invalid_pointer_raises(self):
        """Pointer without leading slash raises."""
        with pytest.raises(JsonPointerError):
            JsonPointer("foo/bar")

    def test_resolve_missing_key_raises(self):
        """Resolving a nonexistent key raises."""
        doc = {"a": 1}
        with pytest.raises(JsonPointerError):
            JsonPointer("/b").resolve(doc)

    def test_resolve_array_out_of_range_raises(self):
        """Resolving an out-of-range array index raises."""
        doc = [1, 2, 3]
        with pytest.raises(JsonPointerError):
            JsonPointer("/5").resolve(doc)
