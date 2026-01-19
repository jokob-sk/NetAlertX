from __future__ import annotations

from typing import Dict, Any, Optional, Type, List
from pydantic import BaseModel


def pydantic_to_json_schema(model: Type[BaseModel], mode: str = "validation") -> Dict[str, Any]:
    """
    Convert a Pydantic model to JSON Schema (OpenAPI 3.1 compatible).

    Uses Pydantic's built-in schema generation which produces
    JSON Schema Draft 2020-12 compatible output.

    Args:
        model: Pydantic BaseModel class
        mode: Schema mode - "validation" (for inputs) or "serialization" (for outputs)

    Returns:
        JSON Schema dictionary
    """
    # Pydantic v2 uses model_json_schema()
    schema = model.model_json_schema(mode=mode)

    # Remove $defs if empty (cleaner output)
    if "$defs" in schema and not schema["$defs"]:
        del schema["$defs"]

    return schema


def build_parameters(entry: Dict[str, Any]) -> List[Dict[str, Any]]:
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


def extract_definitions(schema: Dict[str, Any], definitions: Dict[str, Any]) -> Dict[str, Any]:
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
            definitions[name] = extract_definitions(definition, definitions)
        del schema["$defs"]

    # Rewrite references
    if "$ref" in schema and schema["$ref"].startswith("#/$defs/"):
        ref_name = schema["$ref"].split("/")[-1]
        schema["$ref"] = f"#/components/schemas/{ref_name}"

    # Recursively process properties
    for key, value in schema.items():
        if isinstance(value, dict):
            schema[key] = extract_definitions(value, definitions)
        elif isinstance(value, list):
            schema[key] = [extract_definitions(item, definitions) for item in value]

    return schema


def build_request_body(
    model: Optional[Type[BaseModel]],
    definitions: Dict[str, Any],
    allow_multipart_payload: bool = False
) -> Optional[Dict[str, Any]]:
    """Build OpenAPI requestBody from Pydantic model."""
    if model is None:
        return None

    schema = pydantic_to_json_schema(model)
    schema = extract_definitions(schema, definitions)

    content = {
        "application/json": {
            "schema": schema
        }
    }

    if allow_multipart_payload:
        content["multipart/form-data"] = {
            "schema": schema
        }

    return {
        "required": True,
        "content": content
    }


def strip_validation(schema: Dict[str, Any]) -> Dict[str, Any]:
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
            k: strip_validation(v) for k, v in clean_schema["properties"].items()
        }

    if "items" in clean_schema:
        clean_schema["items"] = strip_validation(clean_schema["items"])

    if "allOf" in clean_schema:
        clean_schema["allOf"] = [strip_validation(x) for x in clean_schema["allOf"]]

    if "anyOf" in clean_schema:
        clean_schema["anyOf"] = [strip_validation(x) for x in clean_schema["anyOf"]]

    if "oneOf" in clean_schema:
        clean_schema["oneOf"] = [strip_validation(x) for x in clean_schema["oneOf"]]

    if "$defs" in clean_schema:
        clean_schema["$defs"] = {
            k: strip_validation(v) for k, v in clean_schema["$defs"].items()
        }

    if "additionalProperties" in clean_schema and isinstance(clean_schema["additionalProperties"], dict):
        clean_schema["additionalProperties"] = strip_validation(clean_schema["additionalProperties"])

    return clean_schema


def build_responses(
    response_model: Optional[Type[BaseModel]], definitions: Dict[str, Any]
) -> Dict[str, Any]:
    """Build OpenAPI responses object."""
    responses = {}

    # Success response (200)
    if response_model:
        # Strip validation from response schema to save tokens
        schema = strip_validation(pydantic_to_json_schema(response_model, mode="serialization"))
        schema = extract_definitions(schema, definitions)
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
