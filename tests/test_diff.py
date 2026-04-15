"""Tests for JSON Patch diff generation."""

import copy

from jsonpatch import diff, apply_patch


class TestDiff:
    def test_equal_documents_empty_patch(self):
        """Equal documents produce an empty patch."""
        assert diff({"a": 1}, {"a": 1}) == []

    def test_diff_simple_replace(self):
        """Changed scalar value produces a replace op."""
        patch = diff({"a": 1}, {"a": 2})
        assert len(patch) == 1
        assert patch[0]["op"] == "replace"
        assert patch[0]["path"] == "/a"

    def test_diff_add_and_remove_keys(self):
        """Detects added and removed keys."""
        src = {"a": 1, "b": 2}
        dst = {"a": 1, "c": 3}
        patch = diff(src, dst)
        ops = {op["op"] for op in patch}
        assert "remove" in ops
        assert "add" in ops

    def test_diff_nested_roundtrip(self):
        """Roundtrip through nested objects."""
        src = {"user": {"name": "Alice", "scores": [90, 85]}}
        dst = {"user": {"name": "Alice", "scores": [90, 95]}}
        patch = diff(src, dst)
        result = apply_patch(copy.deepcopy(src), patch)
        assert result == dst

    def test_diff_list_replace_element(self):
        """Diff replaces individual list elements."""
        src = [1, 2, 3]
        dst = [1, 99, 3]
        patch = diff(src, dst)
        result = apply_patch(copy.deepcopy(src), patch)
        assert result == dst

    def test_diff_detects_move(self):
        """Diff generates move ops when values shift between keys."""
        src = {"a": {"x": 1}, "b": "hello"}
        dst = {"c": {"x": 1}, "b": "hello"}
        patch = diff(src, dst)
        move_ops = [op for op in patch if op["op"] == "move"]
        assert len(move_ops) == 1
        assert move_ops[0]["from"] == "/a"
        assert move_ops[0]["path"] == "/c"

    def test_diff_roundtrip_tilde_digit_keys(self):
        """Keys with ~ followed by digits must roundtrip correctly."""
        src = {"rate~0": 0.5, "version~1": "alpha"}
        dst = {"rate~0": 0.75, "version~1": "beta"}
        patch = diff(src, dst)
        result = apply_patch(copy.deepcopy(src), patch)
        assert result == dst
