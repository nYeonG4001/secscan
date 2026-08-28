from __future__ import annotations

from contextlib import contextmanager
from threading import Lock
from typing import Iterator


class UploadInProgressError(Exception):
    """프로젝트에 이미 진행 중인 업로드가 있을 때 발생한다."""


class ProjectUploadLocks:
    """단일 인스턴스 MVP용 프로세스 내 프로젝트별 비차단 업로드 잠금이다."""

    def __init__(self) -> None:
        self._registry_lock = Lock()
        self._locks: dict[int, Lock] = {}

    @contextmanager
    def acquire(self, project_id: int) -> Iterator[None]:
        lock = self._lock_for(project_id)
        if not lock.acquire(blocking=False):
            raise UploadInProgressError()
        try:
            yield
        finally:
            lock.release()

    def is_locked(self, project_id: int) -> bool:
        lock = self._lock_for(project_id)
        acquired = lock.acquire(blocking=False)
        if acquired:
            lock.release()
        return not acquired

    def _lock_for(self, project_id: int) -> Lock:
        if isinstance(project_id, bool) or not isinstance(project_id, int) or project_id <= 0:
            raise ValueError("The project id must be a positive integer.")
        with self._registry_lock:
            return self._locks.setdefault(project_id, Lock())
