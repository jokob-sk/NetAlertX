#!/usr/bin/env python
"""
NetAlertX OpenAPI Specification Generator

This module provides a registry-based approach to OpenAPI spec generation.
It converts Pydantic models to JSON Schema and assembles a complete OpenAPI 3.1 spec.

Key Features:
- Automatic Pydantic -> JSON Schema conversion
- Centralized endpoint registry
- Unique operationId enforcement
- Complete request/response schema generation

Usage:
    from spec_generator import registry, generate_openapi_spec, register_tool

    # Register endpoints (typically done at module load)
    register_tool(
        path="/devices/search",
        method="POST",
        operation_id="search_devices",
        description="Search for devices",
        request_model=DeviceSearchRequest,
        response_model=DeviceSearchResponse
    )

    # Generate spec (called by MCP endpoint)
    spec = generate_openapi_spec()
"""

from __future__ import annotations

import threading
import json
import inspect
from functools import wraps
from typing import Optional, Type, Any, Dict, List, Literal, Callable
from flask import request, jsonify
from pydantic import BaseModel, ValidationError
from werkzeug.exceptions import BadRequest
import graphene

from logger import mylog

# Thread-safe registry
_registry: List[Dict[str, Any]] = []
_registry_lock = threading.Lock()
_rebuild_lock = threading.Lock()
_operation_ids: set = set()
_disabled_tools: set = set()

# =============================================================================
# VALIDATION DECORATOR (Merged from validation.py)
# =============================================================================

def _handle_validation_error(e: ValidationError, operation_id: str, validation_error_code: int):
    """Internal helper to format Pydantic validation errors."""
    mylog("verbose", [f"[Validation] Error for {operation_id}: {e}"])
    
    # Construct a legacy-compatible error message if possible
    error_msg = "Validation Error"
    if e.errors():
        err = e.errors()[0]
        if err['type'] == 'missing':
            error_msg = f"Missing required '{err['loc'][0]}'"
        else:
            error_msg = f"Validation Error: {err['msg']}"

    return jsonify({
        "success": False,
        "error": error_msg,
        "details": json.loads(e.json())
    }), validation_error_code


def validate_request(
    operation_id: str,
    summary: str,
    description: str,
    request_model: Optional[Type[BaseModel]] = None,
    response_model: Optional[Type[BaseModel]] = None,
    tags: Optional[list[str]] = None,
    path_params: Optional[list[dict]] = None,
    query_params: Optional[list[dict]] = None,
    validation_error_code: int = 422,
    auth_callable: Optional[Callable[[], bool]] = None,
    allow_multipart_payload: bool = False
):
    """
    Decorator to register a Flask route with the OpenAPI registry and validate incoming requests.

    Features:
    - Auto-registers the endpoint with the OpenAPI spec generator.
    - Validates JSON body against `request_model` (for POST/PUT).
    - Injects the validated Pydantic model as the first argument to the view function.
    - Supports auth_callable to check permissions before validation.
    - Returns 422 (default) if validation fails.
    - allow_multipart_payload: If True, allows multipart/form-data and attempts validation from form fields.
    """
    
    def decorator(f: Callable) -> Callable:
        # Detect if f accepts 'payload' argument (unwrap if needed)
        real_f = inspect.unwrap(f)
        sig = inspect.signature(real_f)
        accepts_payload = 'payload' in sig.parameters

        f._openapi_metadata = {
            "operation_id": operation_id,
            "summary": summary,
            "description": description,
            "request_model": request_model,
            "response_model": response_model,
            "tags": tags,
            "path_params": path_params,
            "query_params": query_params
        }

        @wraps(f)
        def wrapper(*args, **kwargs):
            # 0. Handle OPTIONS explicitly if it reaches here (CORS preflight)
            if request.method == "OPTIONS":
                return jsonify({"success": True}), 200

            # 1. Check Authorization first (Coderabbit fix)
            if auth_callable and not auth_callable():
                return jsonify({"success": False, "message": "ERROR: Not authorized", "error": "Forbidden"}), 403

            validated_instance = None

            # 2. Payload Validation
            if request_model:
                if request.method in ["POST", "PUT", "PATCH"]:
                    # Explicit multipart handling (Coderabbit fix)
                    if request.files:
                        if allow_multipart_payload:
                            # Attempt validation from form data if allowed
                            try:
                                data = request.form.to_dict()
                                validated_instance = request_model(**data)
                            except Exception as e:
                                mylog("verbose", [f"[Validation] Multipart validation failed for {operation_id}: {e}"])
                                # We continue without a validated instance but don't fail hard 
                                # as the handler might want to process files manually
                                pass
                        else:
                            # If multipart is not allowed but files are present, we fail fast
                            # This prevents handlers from receiving unexpected None payloads
                            mylog("verbose", [f"[Validation] Multipart bypass attempted for {operation_id} but not allowed."])
                            return jsonify({
                                "success": False, 
                                "error": "Invalid Content-Type", 
                                "message": "Multipart requests are not allowed for this endpoint"
                            }), 415
                    else:
                        if not request.is_json and request.content_length:
                            return jsonify({"success": False, "error": "Invalid Content-Type", "message": "Content-Type must be application/json"}), 415

                        try:
                            data = request.get_json(silent=True) or {}
                            validated_instance = request_model(**data)
                        except ValidationError as e:
                            return _handle_validation_error(e, operation_id, validation_error_code)
                        except BadRequest as e:
                            mylog("verbose", [f"[Validation] Invalid JSON for {operation_id}: {e}"])
                            return jsonify({
                                "success": False,
                                "error": "Invalid JSON",
                                "message": "Request body must be valid JSON"
                            }), 400
                        except Exception as e:
                            mylog("verbose", [f"[Validation] Malformed request for {operation_id}: {e}"])
                            return jsonify({
                                "success": False,
                                "error": "Invalid Request",
                                "message": "Unable to process request body"
                            }), 400
                elif request.method == "GET":
                    # Attempt to validate from query parameters for GET requests
                    try:
                        # request.args is a MultiDict; to_dict() gives first value of each key
                        # which is usually what we want for Pydantic models.
                        data = request.args.to_dict()
                        validated_instance = request_model(**data)
                    except ValidationError as e:
                        return _handle_validation_error(e, operation_id, validation_error_code)
                    except Exception as e:
                        mylog("verbose", [f"[Validation] Query param validation failed for {operation_id}: {e}"])
                        pass

            if validated_instance:
                if accepts_payload:
                    kwargs['payload'] = validated_instance
                else:
                    # Fail fast if decorated function doesn't accept payload (Coderabbit fix)
                    mylog("minimal", [f"[Validation] Endpoint {operation_id} does not accept 'payload' argument!"])
                    raise TypeError(f"Function {f.__name__} (operationId: {operation_id}) does not accept 'payload' argument.")

            return f(*args, **kwargs)

        return wrapper
    return decorator


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
            tools.append({
                "operation_id": entry["operation_id"],
                "summary": entry["summary"],
                "disabled": entry["operation_id"] in disabled_snapshot
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
    original_operation_id: Optional[str] = None
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
            "deprecated": deprecated
        })


def clear_registry() -> None:
    """Clear all registered endpoints (useful for testing)."""
    with _registry_lock:
        _registry.clear()
        _operation_ids.clear()
        _disabled_tools.clear()


def get_registry() -> List[Dict[str, Any]]:
    """Get a copy of the current registry."""
    with _registry_lock:
        return _registry.copy()


def pydantic_to_json_schema(model: Type[BaseModel]) -> Dict[str, Any]:
    """
    Convert a Pydantic model to JSON Schema (OpenAPI 3.1 compatible).

    Uses Pydantic's built-in schema generation which produces
    JSON Schema Draft 2020-12 compatible output.

    Args:
        model: Pydantic BaseModel class

    Returns:
        JSON Schema dictionary
    """
    # Pydantic v2 uses model_json_schema()
    schema = model.model_json_schema(mode="serialization")

    # Remove $defs if empty (cleaner output)
    if "$defs" in schema and not schema["$defs"]:
        del schema["$defs"]

    return schema


def _build_parameters(entry: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Build OpenAPI parameters array from path and query params."""
    parameters = []

    # Path parameters
    for param in entry.get("path_params", []):
        parameters.append({
            "name": param["name"],
            "in": "path",
            "required": True,
            "description": param.get("description", ""),
            "schema": param.get("schema", {"type": "string"})
        })

    # Query parameters
    for param in entry.get("query_params", []):
        parameters.append({
            "name": param["name"],
            "in": "query",
            "required": param.get("required", False),
            "description": param.get("description", ""),
            "schema": param.get("schema", {"type": "string"})
        })

    return parameters


def _extract_definitions(schema: Dict[str, Any], definitions: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively extract $defs from a schema and move them to the definitions dict.
    Also rewrite $ref to point to #/components/schemas/.
    """
    if not isinstance(schema, dict):
        return schema

    # Extract definitions
    if "$defs" in schema:
        for name, definition in schema["$defs"].items():
            # Recursively process the definition itself before adding it
            definitions[name] = _extract_definitions(definition, definitions)
        del schema["$defs"]

    # Rewrite references
    if "$ref" in schema and schema["$ref"].startswith("#/$defs/"):
        ref_name = schema["$ref"].split("/")[-1]
        schema["$ref"] = f"#/components/schemas/{ref_name}"

    # Recursively process properties
    for key, value in schema.items():
        if isinstance(value, dict):
            schema[key] = _extract_definitions(value, definitions)
        elif isinstance(value, list):
            schema[key] = [_extract_definitions(item, definitions) for item in value]

    return schema


def _build_request_body(model: Optional[Type[BaseModel]], definitions: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Build OpenAPI requestBody from Pydantic model."""
    if model is None:
        return None

    schema = pydantic_to_json_schema(model)
    schema = _extract_definitions(schema, definitions)

    return {
        "required": True,
        "content": {
            "application/json": {
                "schema": schema
            }
        }
    }


def _build_responses(
    response_model: Optional[Type[BaseModel]], definitions: Dict[str, Any]
) -> Dict[str, Any]:
    """Build OpenAPI responses object."""
    responses = {}

    # Success response (200)
    if response_model:
        # Strip validation from response schema to save tokens
        schema = _strip_validation(pydantic_to_json_schema(response_model))
        schema = _extract_definitions(schema, definitions)
        responses["200"] = {
            "description": "Successful response",
            "content": {
                "application/json": {
                    "schema": schema
                }
            }
        }
    else:
        responses["200"] = {
            "description": "Successful response",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "success": {"type": "boolean"},
                            "message": {"type": "string"}
                        }
                    }
                }
            }
        }

    # Standard error responses - MINIMIZED context
    # Annotate that these errors can occur, but provide no schema/content to save tokens.
    # The LLM knows what "Bad Request" or "Not Found" means.
    error_codes = {
        "400": "Bad Request",
        "401": "Unauthorized",
        "403": "Forbidden",
        "404": "Not Found",
        "422": "Validation Error",
        "500": "Internal Server Error"
    }

    for code, desc in error_codes.items():
        responses[code] = {
            "description": desc
            # No "content" schema provided
        }

    return responses


def _strip_validation(schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively remove validation constraints from a JSON schema.
    Keeps structure and descriptions, but removes pattern, minLength, etc.
    This saves context tokens for LLMs which don't validate server output.
    """
    if not isinstance(schema, dict):
        return schema

    # Keys to remove
    validation_keys = [
        "pattern", "minLength", "maxLength", "minimum", "maximum",
        "exclusiveMinimum", "exclusiveMaximum", "multipleOf", "minItems",
        "maxItems", "uniqueItems", "minProperties", "maxProperties"
    ]

    clean_schema = {k: v for k, v in schema.items() if k not in validation_keys}

    # Recursively clean sub-schemas
    if "properties" in clean_schema:
        clean_schema["properties"] = {
            k: _strip_validation(v) for k, v in clean_schema["properties"].items()
        }

    if "items" in clean_schema:
        clean_schema["items"] = _strip_validation(clean_schema["items"])

    if "allOf" in clean_schema:
        clean_schema["allOf"] = [_strip_validation(x) for x in clean_schema["allOf"]]

    if "anyOf" in clean_schema:
        clean_schema["anyOf"] = [_strip_validation(x) for x in clean_schema["anyOf"]]

    if "oneOf" in clean_schema:
        clean_schema["oneOf"] = [_strip_validation(x) for x in clean_schema["oneOf"]]

    if "$defs" in clean_schema:
        clean_schema["$defs"] = {
            k: _strip_validation(v) for k, v in clean_schema["$defs"].items()
        }

    return clean_schema


def _flatten_defs(spec: Dict[str, Any]) -> None:
    """
    Experimental: Flatten $defs if they are single-use or small.
    This is complex in pure Python without deep traversal logic.
    For now, we will rely on Pydantic's optimized output, but ensures
    we strip unused defs if any remain.
    """
    pass


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
                path = str(rule).replace("<", "{").replace(">", "}")
                
                # Check if this operation (path + method) is already registered
                op_key = f"{method}:{path}"
                if op_key in registered_ops:
                    continue
                
                # Determine tags
                tags = metadata.get("tags") or ["rest"]
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
                    tags=tags
                )
                registered_ops.add(op_key)

def generate_openapi_spec(
    title: str = "NetAlertX API",
    version: str = "2.0.0",
    description: str = "NetAlertX Network Monitoring API - MCP Compatible",
    servers: Optional[List[Dict[str, str]]] = None,
    flask_app: Optional[Any] = None
) -> Dict[str, Any]:
    """Assemble a complete OpenAPI specification from the registered endpoints."""
    
    # If no app provided and registry is empty, try to use the one from api_server_start
    if not flask_app and not _registry:
        try:
            from .api_server_start import app as start_app
            flask_app = start_app
        except (ImportError, AttributeError):
            pass

    # If we are in "dynamic mode", we rebuild the registry from code
    if flask_app:
        with _rebuild_lock:
            from .graphql_endpoint import devicesSchema
            clear_registry()
            introspect_graphql_schema(devicesSchema)
            introspect_flask_app(flask_app)

    spec = {
        "openapi": "3.1.0",
        "info": {
            "title": title,
            "version": version,
            "description": description,
            "contact": {
                "name": "NetAlertX",
                "url": "https://github.com/jokob-sk/NetAlertX"
            }
        },
        "servers": servers or [{"url": "/", "description": "Local server"}],
        "security": [
            {"BearerAuth": []}
        ],
        "components": {
            "securitySchemes": {
                "BearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "description": "API token from NetAlertX settings (API_TOKEN)"
                }
            },
            "schemas": {}
        },
        "paths": {},
        "tags": []
    }

    definitions = {}

    # Collect unique tags
    tag_set = set()

    with _registry_lock:
        disabled_snapshot = _disabled_tools.copy()
        for entry in _registry:
            path = entry["path"]
            method = entry["method"].lower()

            # Initialize path if not exists
            if path not in spec["paths"]:
                spec["paths"][path] = {}

            # Build operation object
            operation = {
                "operationId": entry["operation_id"],
                "summary": entry["summary"],
                "description": entry["description"],
                "tags": entry["tags"],
                "deprecated": entry["deprecated"]
            }

            # Inject disabled status if applicable
            if entry["operation_id"] in disabled_snapshot:
                operation["x-mcp-disabled"] = True

            # Inject original ID if suffixed (Coderabbit fix)
            if entry.get("original_operation_id"):
                operation["x-original-operationId"] = entry["original_operation_id"]

            # Add parameters (path + query)
            parameters = _build_parameters(entry)
            if parameters:
                operation["parameters"] = parameters

            # Add request body for POST/PUT/PATCH
            if method in ("post", "put", "patch") and entry.get("request_model"):
                request_body = _build_request_body(entry["request_model"], definitions)
                if request_body:
                    operation["requestBody"] = request_body

            # Add responses
            operation["responses"] = _build_responses(
                entry.get("response_model"), definitions
            )

            spec["paths"][path][method] = operation

            # Collect tags
            for tag in entry["tags"]:
                tag_set.add(tag)

    spec["components"]["schemas"] = definitions

    # Build tags array with descriptions
    tag_descriptions = {
        "devices": "Device management and queries",
        "nettools": "Network diagnostic tools",
        "events": "Event and alert management",
        "sessions": "Session history tracking",
        "messaging": "In-app notifications",
        "settings": "Configuration management",
        "sync": "Data synchronization",
        "logs": "Log file access",
        "dbquery": "Direct database queries"
    }

    spec["tags"] = [
        {"name": tag, "description": tag_descriptions.get(tag, f"{tag.title()} operations")}
        for tag in sorted(tag_set)
    ]

    return spec


# Initialize registry on module load
# Registry is now populated dynamically via introspection in generate_openapi_spec
def _register_all_endpoints():
    """Dummy function for compatibility with legacy tests."""
    pass
