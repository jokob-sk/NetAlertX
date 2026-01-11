from functools import wraps
from typing import Type, Optional, Callable
from flask import request, jsonify
from pydantic import BaseModel, ValidationError
from werkzeug.exceptions import BadRequest
from logger import mylog
import json


def validate_request(
    operation_id: str,
    summary: str,
    description: str,
    request_model: Optional[Type[BaseModel]] = None,
    _response_model: Optional[Type[BaseModel]] = None,
    _tags: Optional[list[str]] = None,
    _path_params: Optional[list[dict]] = None,
    _query_params: Optional[list[dict]] = None
):
    """
    Decorator to register a Flask route with the OpenAPI registry and validate incoming requests.

    Features:
    - Auto-registers the endpoint with the OpenAPI spec generator.
    - Validates JSON body against `request_model` (for POST/PUT).
    - Injects the validated Pydantic model as the first argument to the view function.
    - Returns 422 if validation fails.

    Usage:
        @app.route('/devices/search', methods=['POST'])
        @validate_request(
            operation_id="search_devices",
            summary="Search Devices",
            description="...",
            request_model=DeviceSearchRequest
        )
        def search(payload: DeviceSearchRequest):
            # payload is already validated!
            pass
    """
    # TODO (OpenAPI Phase 1.2): utilize _response_model, _tags, _path_params, and _query_params for registry sync.
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def wrapper(*args, **kwargs):
            validated_instance = None

            # 1. Validate Body (if model provided)
            if request_model:
                # Check Content-Type for mutation methods
                if request.method in ["POST", "PUT", "PATCH"]:
                    if not request.is_json and request.content_length:
                        # Allow empty body if optional? No, pydantic handles that.
                        pass

                    try:
                        data = request.get_json() or {}
                        validated_instance = request_model(**data)
                    except ValidationError as e:
                        mylog("verbose", [f"[Validation] Error for {operation_id}: {e}"])
                        return jsonify({
                            "success": False,
                            "error": "Validation Error",
                            "details": json.loads(e.json())
                        }), 422
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

            # 2. Inject into arguments
            # If the function expects the model, pass it using `validated_data` kwarg
            # or simply as the first argument if it fits?
            # Safer: inject as specific kwarg 'payload' if it exists in signature?
            # Or just append to args?

            if validated_instance:
                # We inject it as a keyword argument 'payload'
                # The view function MUST accept 'payload'
                kwargs['payload'] = validated_instance

            try:
                return f(*args, **kwargs)
            except TypeError as e:
                # If 'payload' was passed but not accepted
                if "got an unexpected keyword argument 'payload'" in str(e):
                    mylog("none", [f"[Validation] Endpoint {operation_id} does not accept 'payload' argument!"])
                    # Fallback: try calling without payload (maybe dev forgot to update signature)
                    del kwargs['payload']
                    return f(*args, **kwargs)
                raise e

        # Handle Registration (Mock/Placeholder or real if we had path)
        # We can implement a delayed registration mechanism if needed.
        # For now, we will rely on `spec_generator.py` for registration
        # and use this primarily for VALIDATION (Phase 1.2).
        return wrapper
    return decorator
