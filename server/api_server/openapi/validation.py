from __future__ import annotations

import inspect
import json
from functools import wraps
from typing import Callable, Optional, Type
from flask import request, jsonify
from pydantic import BaseModel, ValidationError
from werkzeug.exceptions import BadRequest

from logger import mylog


def _handle_validation_error(e: ValidationError, operation_id: str, validation_error_code: int):
    """Internal helper to format Pydantic validation errors."""
    mylog("verbose", [f"[Validation] Error for {operation_id}: {e}"])

    # Construct a legacy-compatible error message if possible
    error_msg = "Validation Error"
    if e.errors():
        err = e.errors()[0]
        if err['type'] == 'missing':
            loc = err.get('loc')
            field_name = loc[0] if loc and len(loc) > 0 else "unknown field"
            error_msg = f"Missing required '{field_name}'"
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
            "query_params": query_params,
            "allow_multipart_payload": allow_multipart_payload
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
                # Helper to detect multipart requests by content-type (not just files)
                is_multipart = (
                    request.content_type and request.content_type.startswith("multipart/")
                )

                if request.method in ["POST", "PUT", "PATCH", "DELETE"]:
                    # Explicit multipart handling (Coderabbit fix)
                    # Check both request.files and content-type for form-only multipart bodies
                    if request.files or is_multipart:
                        if allow_multipart_payload:
                            # Attempt validation from form data if allowed
                            try:
                                data = request.form.to_dict()
                                validated_instance = request_model(**data)
                            except ValidationError as e:
                                mylog("verbose", [f"[Validation] Multipart validation failed for {operation_id}: {e}"])
                                # Only continue without validation if handler doesn't expect payload
                                if accepts_payload:
                                    return _handle_validation_error(e, operation_id, validation_error_code)
                                # Otherwise, handler will process files manually
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
                            data = request.get_json(silent=False) or {}
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
                        except (TypeError, KeyError, AttributeError) as e:
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
                    except (TypeError, ValueError, KeyError) as e:
                        mylog("verbose", [f"[Validation] Query param validation failed for {operation_id}: {e}"])
                        return jsonify({
                            "success": False,
                            "error": "Invalid query parameters",
                            "message": "Unable to process query parameters"
                        }), 400
                else:
                    # Unsupported HTTP method with a request_model - fail explicitly
                    mylog("verbose", [f"[Validation] Unsupported HTTP method {request.method} for {operation_id} with request_model"])
                    return jsonify({
                        "success": False,
                        "error": "Method Not Allowed",
                        "message": f"HTTP method {request.method} is not supported for this endpoint"
                    }), 405

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
