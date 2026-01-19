from __future__ import annotations

import threading
from copy import deepcopy
from typing import List, Dict, Any, Literal, Optional, Type, Set
from pydantic import BaseModel

# Thread-safe registry
_registry: List[Dict[str, Any]] = []
_registry_lock = threading.Lock()
_operation_ids: Set[str] = set()
_disabled_tools: Set[str] = set()


class DuplicateOperationIdError(Exception):
    """Raised when an operationId is registered more than once."""
    pass


def set_tool_disabled(operation_id: str, disabled: bool = True) -> bool:
    """
    Enable or disable a tool by operation_id.

    Args:
        operation_id: The unique operation_id of the tool
        disabled: True to disable, False to enable

    Returns:
        bool: True if operation_id exists, False otherwise
    """
    with _registry_lock:
        if operation_id not in _operation_ids:
            return False

        if disabled:
            _disabled_tools.add(operation_id)
        else:
            _disabled_tools.discard(operation_id)
        return True


def is_tool_disabled(operation_id: str) -> bool:
    """
    Check if a tool is disabled.
    Checks both the unique operation_id and the original_operation_id.
    """
    with _registry_lock:
        if operation_id in _disabled_tools:
            return True

        # Also check if the original base ID is disabled
        for entry in _registry:
            if entry["operation_id"] == operation_id:
                orig_id = entry.get("original_operation_id")
                if orig_id and orig_id in _disabled_tools:
                    return True
        return False


def get_disabled_tools() -> List[str]:
    """Get list of all disabled operation_ids."""
    with _registry_lock:
        return list(_disabled_tools)


def get_tools_status() -> List[Dict[str, Any]]:
    """
    Get a list of all registered tools and their disabled status.
    Useful for backend-to-frontend communication.
    """
    tools = []
    with _registry_lock:
        disabled_snapshot = _disabled_tools.copy()
        for entry in _registry:
            op_id = entry["operation_id"]
            orig_id = entry.get("original_operation_id")
            is_disabled = bool(op_id in disabled_snapshot or (orig_id and orig_id in disabled_snapshot))
            tools.append({
                "operation_id": op_id,
                "summary": entry["summary"],
                "disabled": is_disabled
            })
    return tools


def register_tool(
    path: str,
    method: Literal["GET", "POST", "PUT", "DELETE", "PATCH"],
    operation_id: str,
    summary: str,
    description: str,
    request_model: Optional[Type[BaseModel]] = None,
    response_model: Optional[Type[BaseModel]] = None,
    path_params: Optional[List[Dict[str, Any]]] = None,
    query_params: Optional[List[Dict[str, Any]]] = None,
    tags: Optional[List[str]] = None,
    deprecated: bool = False,
    original_operation_id: Optional[str] = None,
    allow_multipart_payload: bool = False
) -> None:
    """
    Register an API endpoint for OpenAPI spec generation.

    Args:
        path: URL path (e.g., "/devices/{mac}")
        method: HTTP method
        operation_id: Unique identifier for this operation (MUST be unique across entire spec)
        summary: Short summary for the operation
        description: Detailed description
        request_model: Pydantic model for request body (POST/PUT/PATCH)
        response_model: Pydantic model for success response
        path_params: List of path parameter definitions
        query_params: List of query parameter definitions
        tags: OpenAPI tags for grouping
        deprecated: Whether this endpoint is deprecated
        original_operation_id: The base ID before suffixing (for disablement mapping)
        allow_multipart_payload: Whether to allow multipart/form-data payloads

    Raises:
        DuplicateOperationIdError: If operation_id already exists in registry
    """
    with _registry_lock:
        if operation_id in _operation_ids:
            raise DuplicateOperationIdError(
                f"operationId '{operation_id}' is already registered. "
                "Each operationId must be unique across the entire API."
            )
        _operation_ids.add(operation_id)

        _registry.append({
            "path": path,
            "method": method.upper(),
            "operation_id": operation_id,
            "original_operation_id": original_operation_id,
            "summary": summary,
            "description": description,
            "request_model": request_model,
            "response_model": response_model,
            "path_params": path_params or [],
            "query_params": query_params or [],
            "tags": tags or ["default"],
            "deprecated": deprecated,
            "allow_multipart_payload": allow_multipart_payload
        })


def clear_registry() -> None:
    """Clear all registered endpoints (useful for testing)."""
    with _registry_lock:
        _registry.clear()
        _operation_ids.clear()
        _disabled_tools.clear()


def get_registry() -> List[Dict[str, Any]]:
    """Get a deep copy of the current registry to prevent external mutation."""
    with _registry_lock:
        return deepcopy(_registry)
