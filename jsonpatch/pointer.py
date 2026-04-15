"""JSON Pointer implementation per RFC 6901.

A JSON Pointer is a string syntax for identifying a specific value
within a JSON document. Example: "/foo/bar/0" identifies the first
element of the array at doc["foo"]["bar"].
"""

from .exceptions import JsonPointerError


def escape_token(token):
    """Escape a JSON Pointer reference token per RFC 6901.

    The '~' character must be escaped as '~0' in reference tokens.
    """
    return str(token).replace("~", "~0")


def unescape_token(token):
    """Unescape a JSON Pointer reference token per RFC 6901.

    Converts '~0' back to '~' in reference tokens.
    """
    return token.replace("~0", "~")


class JsonPointer:
    """Represents a parsed JSON Pointer (RFC 6901).

    Usage:
        ptr = JsonPointer("/foo/bar/0")
        value = ptr.resolve(document)
        parent, key = ptr.resolve_parent(document)
    """

    def __init__(self, path: str):
        """Parse a JSON Pointer string.

        Args:
            path: A JSON Pointer string. Empty string refers to the
                  whole document. Must start with '/' if non-empty.

        Raises:
            JsonPointerError: If the pointer syntax is invalid.
        """
        self.path = path

        if path == "":
            self.parts = []
            return

        if not path.startswith("/"):
            raise JsonPointerError(
                f"JSON Pointer must start with '/' or be empty: {path!r}"
            )

        # Split into reference tokens and unescape per RFC 6901
        self.parts = [unescape_token(p) for p in path.split("/")[1:]]

    def resolve(self, doc):
        """Resolve this pointer against a JSON document.

        Args:
            doc: The JSON document (dict, list, or scalar).

        Returns:
            The value at the pointer location.

        Raises:
            JsonPointerError: If the pointer cannot be resolved.
        """
        if not self.parts:
            return doc

        current = doc
        for i, part in enumerate(self.parts):
            current = self._resolve_token(current, part, i)

        return current

    def resolve_parent(self, doc):
        """Resolve to the parent container and return (parent, last_token).

        This is useful for operations that need to modify the value
        at the pointer location (add, remove, replace).

        Args:
            doc: The JSON document.

        Returns:
            Tuple of (parent_container, last_token).

        Raises:
            JsonPointerError: If the pointer is empty (root has no parent)
                or the parent path cannot be resolved.
        """
        if not self.parts:
            raise JsonPointerError("Root pointer has no parent")

        if len(self.parts) == 1:
            return doc, self.parts[0]

        current = doc
        for i, part in enumerate(self.parts[:-1]):
            current = self._resolve_token(current, part, i)

        return current, self.parts[-1]

    def _resolve_token(self, current, token, depth):
        """Resolve a single token against the current document node.

        Args:
            current: Current node in the document tree.
            token: The reference token to resolve.
            depth: Current depth (for error messages).

        Returns:
            The child node identified by the token.

        Raises:
            JsonPointerError: If the token cannot be resolved.
        """
        if isinstance(current, dict):
            if token not in current:
                raise JsonPointerError(
                    f"Key {token!r} not found at depth {depth}"
                )
            return current[token]

        elif isinstance(current, list):
            if token == "-":
                raise JsonPointerError(
                    "'-' token refers to nonexistent element past end of array"
                )
            try:
                idx = int(token)
            except ValueError:
                raise JsonPointerError(
                    f"Invalid array index {token!r} at depth {depth}"
                )
            if idx < 0 or idx >= len(current):
                raise JsonPointerError(
                    f"Array index {idx} out of range (length {len(current)})"
                )
            return current[idx]

        else:
            raise JsonPointerError(
                f"Cannot index into {type(current).__name__} at depth {depth}"
            )

    def __str__(self):
        return self.path

    def __repr__(self):
        return f"JsonPointer({self.path!r})"

    def __eq__(self, other):
        if isinstance(other, JsonPointer):
            return self.path == other.path
        return NotImplemented

    def __hash__(self):
        return hash(self.path)
