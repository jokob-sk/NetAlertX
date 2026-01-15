"""
SSE (Server-Sent Events) Endpoint
Provides real-time state updates to frontend via HTTP streaming
Reduces polling overhead from 60+ requests/minute to 1 persistent connection
"""

import json
import threading
import time
from collections import deque
from flask import Response, request, jsonify
from logger import mylog

# Thread-safe event queue
_event_queue = deque(maxlen=100)  # Keep last 100 events
_queue_lock = threading.Lock()
_subscribers = set()  # Track active subscribers
_subscribers_lock = threading.Lock()


class StateChangeEvent:
    """Represents a state change event to broadcast"""

    def __init__(self, event_type: str, data: dict, timestamp: float = None):
        self.event_type = event_type  # 'state_update', 'settings_changed', 'device_update', etc
        self.data = data
        self.timestamp = timestamp or time.time()
        self.id = int(self.timestamp * 1000)  # Use millisecond timestamp as ID

    def to_sse_format(self) -> str:
        """Convert to SSE format with error handling"""
        try:
            return f"id: {self.id}\nevent: {self.event_type}\ndata: {json.dumps(self.data)}\n\n"
        except Exception as e:
            mylog("none", [f"[SSE] Failed to serialize event: {e}"])
            return ""


def broadcast_event(event_type: str, data: dict) -> None:
    """
    Broadcast an event to all connected SSE clients
    Called by backend when state changes occur
    """
    try:
        event = StateChangeEvent(event_type, data)
        with _queue_lock:
            _event_queue.append(event)
        mylog("debug", [f"[SSE] Broadcasted event: {event_type}"])
    except Exception as e:
        mylog("none", [f"[SSE] Failed to broadcast event: {e}"])


def register_subscriber(client_id: str) -> None:
    """Track new SSE subscriber"""
    with _subscribers_lock:
        _subscribers.add(client_id)
    mylog("debug", [f"[SSE] Subscriber registered: {client_id} (total: {len(_subscribers)})"])


def unregister_subscriber(client_id: str) -> None:
    """Track disconnected SSE subscriber"""
    with _subscribers_lock:
        _subscribers.discard(client_id)
    mylog(
        "debug",
        [f"[SSE] Subscriber unregistered: {client_id} (remaining: {len(_subscribers)})"],
    )


def get_subscriber_count() -> int:
    """Get number of active SSE connections"""
    with _subscribers_lock:
        return len(_subscribers)


def sse_stream(client_id: str):
    """
    Generator for SSE stream
    Yields events to client with reconnect guidance
    """
    register_subscriber(client_id)

    # Send initial connection message
    yield "id: 0\nevent: connected\ndata: {}\nretry: 3000\n\n"

    # Send initial unread notifications count on connect
    try:
        from messaging.in_app import get_unread_notifications
        initial_notifications = get_unread_notifications().json
        unread_count = len(initial_notifications) if isinstance(initial_notifications, list) else 0
        broadcast_event("unread_notifications_count_update", {"count": unread_count})
    except Exception as e:
        mylog("debug", [f"[SSE] Failed to broadcast initial unread count: {e}"])

    last_event_id = 0

    try:
        while True:
            # Check for new events since last_event_id
            with _queue_lock:
                new_events = [
                    e for e in _event_queue if e.id > last_event_id
                ]

            if new_events:
                for event in new_events:
                    sse_data = event.to_sse_format()
                    if sse_data:
                        yield sse_data
                    last_event_id = event.id
            else:
                # Send keepalive every 30 seconds to prevent connection timeout
                time.sleep(1)
                if int(time.time()) % 30 == 0:
                    yield ": keepalive\n\n"

    except GeneratorExit:
        unregister_subscriber(client_id)
    except Exception as e:
        mylog("none", [f"[SSE] Stream error for {client_id}: {e}"])
        unregister_subscriber(client_id)


def create_sse_endpoint(app, is_authorized=None) -> None:
    """Mount SSE endpoints to Flask app - /sse/state and /sse/stats

    Args:
        app: Flask app instance
        is_authorized: Optional function to check authorization (if None, allows all)
    """

    @app.route("/sse/state", methods=["GET", "OPTIONS"])
    def api_sse_state():
        if request.method == "OPTIONS":
            return jsonify({"success": True}), 200

        if is_authorized and not is_authorized():
            return {"success": False, "error": "Unauthorized"}, 401

        client_id = request.args.get("client", f"client-{int(time.time() * 1000)}")
        mylog("debug", [f"[SSE] Client connected: {client_id}"])

        return Response(
            sse_stream(client_id),
            mimetype="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
                "Connection": "keep-alive",
            },
        )

    @app.route("/sse/stats", methods=["GET", "OPTIONS"])
    def api_sse_stats():
        """Get SSE endpoint statistics for debugging"""
        if request.method == "OPTIONS":
            return jsonify({"success": True}), 200

        if is_authorized and not is_authorized():
            return {"none": "Unauthorized"}, 401

        return {
            "success": True,
            "connected_clients": get_subscriber_count(),
            "queued_events": len(_event_queue),
            "max_queue_size": _event_queue.maxlen,
        }

    mylog("info", ["[SSE] Endpoints mounted: /sse/state, /sse/stats"])
