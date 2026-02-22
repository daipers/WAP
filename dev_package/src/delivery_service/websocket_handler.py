"""
websocket_handler.py
====================

WebSocket handler for real-time assessment delivery.
Provides timer synchronization and message handling.

Features:
- Server-authoritative timer that continues even when client disconnects
- Message types: answer_save, navigate, ping
- Timer sync broadcasts every second
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, Optional, Set

from fastapi import WebSocket

from .session_manager import SessionManager, SessionState


logger = logging.getLogger(__name__)


class DeliveryWebSocketHandler:
    """
    WebSocket handler for delivery service.

    Manages real-time timer synchronization and message handling
    for assessment sessions.
    """

    def __init__(self, session_manager: SessionManager):
        """
        Initialize the handler.

        Args:
            session_manager: The session manager instance
        """
        self.session_manager = session_manager
        self._active_connections: Dict[str, Set[WebSocket]] = {}
        self._timer_tasks: Dict[str, asyncio.Task] = {}

    async def handle_connection(self, websocket: WebSocket, session_id: str) -> None:
        """
        Handle a WebSocket connection.

        Validates the session exists and starts the timer sync.

        Args:
            websocket: The WebSocket connection
            session_id: The session ID to connect to
        """
        # Validate session exists
        if not self.session_manager.session_exists(session_id):
            await websocket.close(code=4004, reason="Session not found")
            return

        # Get session to verify it's in a valid state
        try:
            session = self.session_manager.get_session(session_id)
        except KeyError:
            await websocket.close(code=4004, reason="Session not found")
            return

        # Check session state allows WebSocket connection
        if session.state not in (SessionState.IN_PROGRESS, SessionState.PAUSED):
            await websocket.close(
                code=4003, reason=f"Session not active (state: {session.state.value})"
            )
            return

        # Accept the connection
        await websocket.accept()

        # Track the connection
        if session_id not in self._active_connections:
            self._active_connections[session_id] = set()
        self._active_connections[session_id].add(websocket)

        logger.info(f"WebSocket connected for session {session_id}")

        # Start timer sync if not already running
        if session_id not in self._timer_tasks:
            self._timer_tasks[session_id] = asyncio.create_task(
                self._timer_sync(session_id)
            )

        try:
            # Handle messages
            await self._handle_messages(websocket, session_id)
        except Exception as e:
            logger.error(f"WebSocket error for session {session_id}: {e}")
        finally:
            # Clean up
            await self._handle_disconnect(websocket, session_id)

    async def _handle_messages(self, websocket: WebSocket, session_id: str) -> None:
        """
        Handle incoming WebSocket messages.

        Args:
            websocket: The WebSocket connection
            session_id: The session ID
        """
        try:
            while True:
                # Wait for message
                data = await websocket.receive_text()

                # Parse JSON
                try:
                    message = json.loads(data)
                except json.JSONDecodeError:
                    await websocket.send_json(
                        {"type": "error", "message": "Invalid JSON"}
                    )
                    continue

                # Handle message based on type
                await self.handle_message(websocket, session_id, message)

        except asyncio.CancelledError:
            # Task was cancelled (client disconnected)
            raise
        except Exception as e:
            logger.error(f"Message handling error: {e}")
            raise

    async def handle_message(
        self,
        websocket: WebSocket,
        session_id: str,
        data: Dict[str, Any],
    ) -> None:
        """
        Process a message from the client.

        Supported message types:
        - ping: Respond with pong and current timer
        - answer_save: Save an answer for an item
        - navigate: Navigate to a different item

        Args:
            websocket: The WebSocket connection
            session_id: The session ID
            data: The message data
        """
        message_type = data.get("type", "")

        if message_type == "ping":
            # Respond with pong and current timer
            await self._send_timer_update(websocket, session_id)

        elif message_type == "answer_save":
            # Save an answer
            await self._handle_answer_save(websocket, session_id, data)

        elif message_type == "navigate":
            # Navigate to a different item
            await self._handle_navigate(websocket, session_id, data)

        elif message_type == "flag":
            # Flag/unflag an item
            await self._handle_flag(websocket, session_id, data)

        elif message_type == "get_current":
            # Get current item info
            await self._send_current_item(websocket, session_id)

        else:
            await websocket.send_json(
                {"type": "error", "message": f"Unknown message type: {message_type}"}
            )

    async def _handle_answer_save(
        self,
        websocket: WebSocket,
        session_id: str,
        data: Dict[str, Any],
    ) -> None:
        """Handle answer save message."""
        item_id = data.get("item_id")
        response = data.get("response", {})

        if not item_id:
            await websocket.send_json({"type": "error", "message": "item_id required"})
            return

        try:
            session = self.session_manager.submit_answer(session_id, item_id, response)
            await websocket.send_json(
                {
                    "type": "answer_saved",
                    "item_id": item_id,
                    "current_index": session.current_item_index,
                }
            )
        except Exception as e:
            await websocket.send_json({"type": "error", "message": str(e)})

    async def _handle_navigate(
        self,
        websocket: WebSocket,
        session_id: str,
        data: Dict[str, Any],
    ) -> None:
        """Handle navigation message."""
        direction = data.get("direction", "next")
        target_index = data.get("target_index")

        try:
            session = self.session_manager.navigate(
                session_id,
                direction=direction,
                target_index=target_index,
            )
            await websocket.send_json(
                {
                    "type": "navigated",
                    "current_index": session.current_item_index,
                    "total_items": session.total_items,
                }
            )
            # Send current item data
            await self._send_current_item(websocket, session_id)
        except ValueError as e:
            await websocket.send_json({"type": "error", "message": str(e)})

    async def _handle_flag(
        self,
        websocket: WebSocket,
        session_id: str,
        data: Dict[str, Any],
    ) -> None:
        """Handle flag message."""
        item_id = data.get("item_id")
        is_flagged = data.get("is_flagged", True)

        if not item_id:
            await websocket.send_json({"type": "error", "message": "item_id required"})
            return

        try:
            session = self.session_manager.get_session(session_id)
            if is_flagged:
                session.flag_item(item_id)
            else:
                session.unflag_item(item_id)

            await websocket.send_json(
                {
                    "type": "flagged",
                    "item_id": item_id,
                    "is_flagged": is_flagged,
                }
            )
        except Exception as e:
            await websocket.send_json({"type": "error", "message": str(e)})

    async def _send_current_item(
        self,
        websocket: WebSocket,
        session_id: str,
    ) -> None:
        """Send current item information."""
        try:
            session = self.session_manager.get_session(session_id)
            current_item = session.current_item

            item_data = None
            if current_item:
                item_data = {
                    "item_id": current_item.item_id,
                    "content": current_item.content,
                    "metadata": current_item.metadata,
                }

            await websocket.send_json(
                {
                    "type": "current_item",
                    "item": item_data,
                    "index": session.current_item_index,
                    "total": session.total_items,
                    "is_flagged": current_item.item_id in session.flagged_items
                    if current_item
                    else False,
                }
            )
        except Exception as e:
            await websocket.send_json({"type": "error", "message": str(e)})

    async def _send_timer_update(
        self,
        websocket: WebSocket,
        session_id: str,
    ) -> None:
        """
        Send a timer update to a specific connection.

        Args:
            websocket: The WebSocket connection
            session_id: The session ID
        """
        try:
            session = self.session_manager.get_session(session_id)
            time_remaining = session.calculate_time_remaining()

            await websocket.send_json(
                {
                    "type": "timer",
                    "time_remaining": time_remaining,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )
        except Exception as e:
            logger.error(f"Error sending timer update: {e}")

    async def _timer_sync(self, session_id: str) -> None:
        """
        Send timer updates to all connected clients every second.

        This runs as a background task and continues even when
        clients disconnect (server-authoritative timing).

        Args:
            session_id: The session ID
        """
        logger.info(f"Starting timer sync for session {session_id}")

        while session_id in self._active_connections:
            # Get all active connections for this session
            connections = list(self._active_connections.get(session_id, []))

            if connections:
                # Check session state
                try:
                    session = self.session_manager.get_session(session_id)

                    # Check for expiration
                    if session.is_time_expired():
                        self.session_manager.update_state(
                            session_id, SessionState.EXPIRED
                        )

                        # Notify all clients
                        for conn in connections:
                            try:
                                await conn.send_json(
                                    {
                                        "type": "expired",
                                        "message": "Time expired",
                                    }
                                )
                            except Exception:
                                pass

                        break

                    # Send timer to all connections
                    time_remaining = session.calculate_time_remaining()
                    for conn in connections:
                        try:
                            await conn.send_json(
                                {
                                    "type": "timer",
                                    "time_remaining": time_remaining,
                                    "timestamp": datetime.utcnow().isoformat(),
                                }
                            )
                        except Exception:
                            pass

                except KeyError:
                    # Session no longer exists
                    break

            # Wait 1 second before next update
            await asyncio.sleep(1)

        # Clean up timer task
        if session_id in self._timer_tasks:
            del self._timer_tasks[session_id]

        logger.info(f"Timer sync ended for session {session_id}")

    async def _handle_disconnect(self, websocket: WebSocket, session_id: str) -> None:
        """
        Handle client disconnection.

        Note: The timer continues running server-side even after
        client disconnects (server-authoritative timing).

        Args:
            websocket: The disconnected WebSocket
            session_id: The session ID
        """
        # Remove the connection
        if session_id in self._active_connections:
            self._active_connections[session_id].discard(websocket)

            # Clean up if no more connections
            if not self._active_connections[session_id]:
                del self._active_connections[session_id]
                # Note: We don't stop the timer task here - it continues
                # server-side for server-authoritative timing

        logger.info(f"WebSocket disconnected for session {session_id}")

        # Log disconnect but don't pause the timer
        try:
            session = self.session_manager.get_session(session_id)
            logger.info(
                f"Session {session_id} still active with "
                f"{session.state.value} state after client disconnect"
            )
        except KeyError:
            pass

    async def broadcast_to_session(
        self,
        session_id: str,
        message: Dict[str, Any],
    ) -> None:
        """
        Broadcast a message to all connected clients for a session.

        Args:
            session_id: The session ID
            message: The message to broadcast
        """
        if session_id not in self._active_connections:
            return

        for conn in list(self._active_connections[session_id]):
            try:
                await conn.send_json(message)
            except Exception as e:
                logger.error(f"Broadcast error: {e}")

    def get_connection_count(self, session_id: str) -> int:
        """Get the number of active connections for a session."""
        return len(self._active_connections.get(session_id, set()))

    def is_timer_running(self, session_id: str) -> bool:
        """Check if the timer sync is running for a session."""
        return session_id in self._timer_tasks

    async def stop_timer(self, session_id: str) -> None:
        """Stop the timer sync for a session."""
        if session_id in self._timer_tasks:
            self._timer_tasks[session_id].cancel()
            try:
                await self._timer_tasks[session_id]
            except asyncio.CancelledError:
                pass
            del self._timer_tasks[session_id]


# ============================================================================
# Helper function for standalone usage
# ============================================================================


async def timer_sync(
    session_manager: SessionManager,
    session_id: str,
    websocket: WebSocket,
) -> None:
    """
    Standalone timer sync function for use with FastAPI.

    This is a simpler version that handles just the timer sync
    for a single WebSocket connection.

    Args:
        session_manager: The session manager
        session_id: The session ID
        websocket: The WebSocket connection
    """
    handler = DeliveryWebSocketHandler(session_manager)

    # Validate session
    if not session_manager.session_exists(session_id):
        await websocket.close(code=4004, reason="Session not found")
        return

    try:
        session = session_manager.get_session(session_id)
    except KeyError:
        await websocket.close(code=4004, reason="Session not found")
        return

    await websocket.accept()

    try:
        while True:
            # Send timer update
            time_remaining = session.calculate_time_remaining()
            await websocket.send_json(
                {
                    "type": "timer",
                    "time_remaining": time_remaining,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )

            # Check for expiration
            if session.is_time_expired():
                await websocket.send_json(
                    {
                        "type": "expired",
                        "message": "Time expired",
                    }
                )
                break

            # Wait 1 second
            await asyncio.sleep(1)

            # Refresh session
            session = session_manager.get_session(session_id)

    except WebSocketDisconnect:
        pass
