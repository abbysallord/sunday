"""Job Manager for background asynchronous tasks."""

import asyncio
from typing import Callable, Dict

from sunday.utils.logging import log


class JobManager:
    """Manages long-running background agent tasks."""

    def __init__(self):
        self._jobs: Dict[str, asyncio.Task] = {}
        self._callbacks: Dict[str, Callable] = {}

    def register_callback(self, session_id: str, callback: Callable) -> None:
        """Register a callback for a specific session (e.g., websocket connection)."""
        self._callbacks[session_id] = callback

    def unregister_callback(self, session_id: str) -> None:
        if session_id in self._callbacks:
            del self._callbacks[session_id]

    async def emit_event(self, session_id: str, event_type: str, data: dict) -> None:
        """Emit an event to the registered callback for a session."""
        callback = self._callbacks.get(session_id)
        if callback:
            try:
                await callback(event_type, data)
            except Exception as e:
                log.error("job_manager.emit_failed", session_id=session_id, error=str(e))
        else:
            log.debug("job_manager.no_callback", session_id=session_id, event=event_type)

    def start_job(self, job_id: str, session_id: str, coro) -> None:
        """Start a background coroutine and track it."""
        if job_id in self._jobs:
            log.warning("job_manager.duplicate_job", job_id=job_id)
            return

        task = asyncio.create_task(self._job_wrapper(job_id, session_id, coro))
        self._jobs[job_id] = task
        log.info("job_manager.started", job_id=job_id)

    async def _job_wrapper(self, job_id: str, session_id: str, coro) -> None:
        try:
            await coro
        except asyncio.CancelledError:
            log.info("job_manager.cancelled", job_id=job_id)
            await self.emit_event(
                session_id, "job_status", {"job_id": job_id, "status": "cancelled"}
            )
        except Exception as e:
            log.error("job_manager.failed", job_id=job_id, error=str(e))
            await self.emit_event(
                session_id, "error", {"job_id": job_id, "message": str(e)}
            )
        finally:
            if job_id in self._jobs:
                del self._jobs[job_id]
            log.info("job_manager.completed", job_id=job_id)


# Global singleton
job_manager = JobManager()
