"""
Integration layer to broadcast state changes via SSE
Call these functions from the backend whenever state changes occur
"""
from logger import mylog
from .sse_endpoint import broadcast_event


def broadcast_state_update(current_state: str, settings_imported: float = None, **kwargs) -> None:
    """
    Broadcast a state update to all connected SSE clients
    Call this from app_state.updateState() or equivalent

    Args:
        current_state: The new application state string
        settings_imported: Optional timestamp of last settings import
        **kwargs: Additional state data to broadcast
    """
    try:
        state_data = {
            "currentState": current_state,
            "timestamp": kwargs.get("timestamp"),
            **({"settingsImported": settings_imported} if settings_imported else {}),
            **{k: v for k, v in kwargs.items() if k not in ["timestamp"]},
        }
        broadcast_event("state_update", state_data)
    except ImportError:
        pass  # SSE not available, silently skip
    except Exception as e:
        mylog("debug", [f"[SSE] Failed to broadcast state update: {e}"])


def broadcast_unread_notifications_count(count: int) -> None:
    """
    Broadcast unread notifications count to all connected SSE clients
    Call this from messaging.in_app functions when notifications change

    Args:
        count: Number of unread notifications (must be int)
    """
    try:
        # Ensure count is an integer
        count = int(count) if count else 0
        broadcast_event("unread_notifications_count_update", {"count": count})
    except ImportError:
        pass  # SSE not available, silently skip
    except Exception as e:
        mylog("debug", [f"[SSE] Failed to broadcast unread count update: {e}"])
