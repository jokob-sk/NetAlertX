# Project Report: OpenAPI Generation via GraphQL Introspection

## 1. Executive Summary
This report outlines the technical strategy to transition the NetAlertX API documentation from a manual, Pydantic-based registry to a dynamic, GraphQL-driven introspection system. By establishing GraphQL as the "Single Source of Truth," we eliminate hardcoded field lists and ensure that both GraphQL and REST documentation stay in sync automatically.

## 2. Current Architecture (As-Is)
*   **REST API:** Uses a manual registry in `spec_generator.py` and Pydantic models in `schemas.py`. It contains rich metadata (descriptions, examples) but is disconnected from the GraphQL logic.
*   **GraphQL API:** Defined in `graphql_endpoint.py` using Graphene. It is isomorphic to the data but lacks the supplemental metadata found in the REST schemas.
*   **Problem:** Maintaining two parallel schemas leads to "documentation drift" and requires manual updates to field lists in both the backend and frontend.

## 3. The Objective (To-Be)
*   **Single Source of Truth:** Move all field descriptions, examples, and tags into the GraphQL schema (`graphql_endpoint.py`).
*   **Dynamic Generation:** Implement a converter that introspects the GraphQL schema and translates it into an OpenAPI 3.1 specification.
*   **Isomorphic UI:** Enable the frontend to use GraphQL introspection to dynamically build tables and forms, removing hardcoded string arrays.

## 4. Implementation Strategy

### Phase 1: Metadata Migration ("The Merge")
Enrich the Graphene types with the "supplemental data" currently in Pydantic models.
*   **Action:** Update `Device`, `Setting`, and other objects in `graphql_endpoint.py`.
*   **Example:** 
    ```python
    # From (Pydantic)
    devMac: str = Field(..., description="Device MAC address")
    # To (Graphene)
    devMac = String(description="Device MAC address")
    ```

### Phase 2: Building the GraphQL-to-OpenAPI Bridge
Create a generator (`server/api_server/introspection_bridge.py`) that:
1.  **Executes Introspection:** Runs a standard `__schema` query against `devicesSchema`.
2.  **Maps Types:** Converts GraphQL Scalars (String, Int, Boolean) to JSON Schema types.
3.  **Resolves Paths:** Uses a mapping configuration to link REST paths to GraphQL Queries/Mutations.
    *   *Path:* `/devices/by-status` -> *Query:* `devices(status: ...)`
4.  **Emits OpenAPI:** Combines the mapped paths and components into a standard `openapi.json`.

### Phase 3: Rerouting & Cleanup
1.  **Reroute docs:** Update the `/mcp/sse/openapi.json` endpoint to use the new introspection bridge.
2.  **Frontend Integration:** Implement a helper (as suggested in the chat) that uses `__type(name: "Device")` to drive UI columns.
3.  **Decommission:** Remove the manual registry in `spec_generator.py`.

## 5. Technical Challenges
*   **Mapping REST Paths:** Unlike GraphQL, REST has explicit URLs. We need a lightweight decorator or mapping object to tell the generator which GraphQL field corresponds to which REST path.
*   **Mutations:** To fully represent the "Write" operations of the REST API (e.g., `/device/update`), these must be added as Graphene `Mutations`.

## 6. Conclusion
Leveraging GraphQL introspection reduces maintenance overhead and provides a "textbook" implementation of a modern, schema-driven API. The frontend becomes resilient to backend changes, and the OpenAPI spec becomes a live reflection of the actual code.
