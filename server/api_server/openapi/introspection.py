from __future__ import annotations

import re
from typing import Any
import graphene

from .registry import register_tool, _operation_ids


def introspect_graphql_schema(schema: graphene.Schema):
    """
    Introspect the GraphQL schema and register endpoints in the OpenAPI registry.
    This bridges the 'living code' (GraphQL) to the OpenAPI spec.
    """
    # Graphene schema introspection
    graphql_schema = schema.graphql_schema
    query_type = graphql_schema.query_type

    if not query_type:
        return

    # We register the main /graphql endpoint once
    register_tool(
        path="/graphql",
        method="POST",
        operation_id="graphql_query",
        summary="GraphQL Endpoint",
        description="Execute arbitrary GraphQL queries against the system schema.",
        tags=["graphql"]
    )


def _flask_to_openapi_path(flask_path: str) -> str:
    """Convert Flask path syntax to OpenAPI path syntax."""
    # Handles <converter:variable> -> {variable} and <variable> -> {variable}
    return re.sub(r'<(?:\w+:)?(\w+)>', r'{\1}', flask_path)


def introspect_flask_app(app: Any):
    """
    Introspect the Flask application to find routes decorated with @validate_request
    and register them in the OpenAPI registry.
    """
    registered_ops = set()
    for rule in app.url_map.iter_rules():
        view_func = app.view_functions.get(rule.endpoint)
        if not view_func:
            continue

        # Check for our decorator's metadata
        metadata = getattr(view_func, "_openapi_metadata", None)
        if not metadata:
            # Fallback for wrapped functions
            if hasattr(view_func, "__wrapped__"):
                metadata = getattr(view_func.__wrapped__, "_openapi_metadata", None)

        if metadata:
            op_id = metadata["operation_id"]

            # Register the tool with real path and method from Flask
            for method in rule.methods:
                if method in ("OPTIONS", "HEAD"):
                    continue

                # Create a unique key for this path/method/op combination if needed,
                # but operationId must be unique globally.
                # If the same function is mounted on multiple paths, we append a suffix
                path = _flask_to_openapi_path(str(rule))

                # Check if this operation (path + method) is already registered
                op_key = f"{method}:{path}"
                if op_key in registered_ops:
                    continue

                # Determine tags - create a copy to avoid mutating shared metadata
                tags = list(metadata.get("tags") or ["rest"])
                if path.startswith("/mcp/"):
                    # Move specific tags to secondary position or just add MCP
                    if "rest" in tags:
                        tags.remove("rest")
                    if "mcp" not in tags:
                        tags.append("mcp")

                # Ensure unique operationId
                original_op_id = op_id
                unique_op_id = op_id
                count = 1
                while unique_op_id in _operation_ids:
                    unique_op_id = f"{op_id}_{count}"
                    count += 1

                register_tool(
                    path=path,
                    method=method,
                    operation_id=unique_op_id,
                    original_operation_id=original_op_id if unique_op_id != original_op_id else None,
                    summary=metadata["summary"],
                    description=metadata["description"],
                    request_model=metadata.get("request_model"),
                    response_model=metadata.get("response_model"),
                    path_params=metadata.get("path_params"),
                    query_params=metadata.get("query_params"),
                    tags=tags,
                    allow_multipart_payload=metadata.get("allow_multipart_payload", False)
                )
                registered_ops.add(op_key)
