"""Custom exceptions for the jsonpatch library."""


class JsonPointerError(Exception):
    """Raised when a JSON Pointer operation fails."""
    pass


class JsonPatchError(Exception):
    """Raised when a JSON Patch operation fails."""
    pass


class JsonPatchTestError(JsonPatchError):
    """Raised when a JSON Patch 'test' operation fails."""
    pass


class JsonPatchConflictError(JsonPatchError):
    """Raised when a JSON Patch operation conflicts with the document."""
    pass
