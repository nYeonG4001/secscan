from __future__ import annotations

import os
import shutil
import tempfile
import uuid
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path, PurePosixPath
from typing import Iterable, Iterator


class SourceWorkspace:
    """서버가 관리하는 staging 및 불투명 프로젝트 소스 디렉터리를 관리한다."""

    def __init__(self, storage_root: Path) -> None:
        if not storage_root.is_absolute():
            raise ValueError("The storage root must be absolute.")
        storage_root.mkdir(mode=0o750, parents=True, exist_ok=True)
        self._root = storage_root.resolve(strict=True)
        if not self._root.is_dir() or self._root.is_symlink():
            raise ValueError("The storage root must be a real directory.")

    @property
    def storage_root(self) -> Path:
        return self._root

    def create_staging_directory(self) -> Path:
        staging_root = self._root / "staging"
        staging_root.mkdir(mode=0o700, parents=True, exist_ok=True)
        return Path(tempfile.mkdtemp(prefix="", dir=staging_root)).resolve(strict=True)

    @contextmanager
    def staging_directory(self) -> Iterator[Path]:
        staging_directory = self.create_staging_directory()
        try:
            yield staging_directory
        finally:
            self.cleanup_staging_directory(staging_directory)

    def cleanup_staging_directory(self, staging_directory: Path) -> None:
        candidate = self._direct_child(staging_directory, self._root / "staging")
        if candidate is None or not candidate.exists() or candidate.is_symlink():
            return
        if candidate.is_dir():
            shutil.rmtree(candidate)

    def promote_staging_directory(self, project_id: int, staging_directory: Path) -> str:
        project_id = _validate_project_id(project_id)
        staging = self._direct_child(staging_directory, self._root / "staging")
        if staging is None or not staging.is_dir() or staging.is_symlink():
            raise ValueError("The staging directory is not managed by this workspace.")

        sources_root = self._root / "projects" / str(project_id) / "sources"
        sources_root.mkdir(mode=0o750, parents=True, exist_ok=True)
        while True:
            source_id = uuid.uuid4().hex
            destination = sources_root / source_id
            if not destination.exists():
                break
        os.replace(staging, destination)
        return self._source_location(project_id, source_id)

    def resolve_source_location(self, source_location: str) -> Path:
        parts = self._source_location_parts(source_location)
        path = self._root.joinpath(*parts)
        try:
            resolved = path.resolve(strict=False)
            resolved.relative_to(self._root)
        except ValueError as exc:
            raise ValueError("The source location is outside this workspace.") from exc
        return resolved

    def reserve_analysis_snapshot(self, analysis_id: int) -> str:
        analysis_id = _validate_project_id(analysis_id)
        snapshot_parent = self._root / "analyses" / str(analysis_id)
        snapshot_parent.mkdir(mode=0o750, parents=True, exist_ok=False)
        return f"analyses/{analysis_id}/source"

    def resolve_analysis_snapshot_location(self, snapshot_location: str) -> Path:
        path = PurePosixPath(snapshot_location)
        parts = path.parts
        if (
            path.is_absolute()
            or len(parts) != 3
            or parts[0] != "analyses"
            or not parts[1].isdigit()
            or int(parts[1]) <= 0
            or parts[2] != "source"
        ):
            raise ValueError("The snapshot location is not managed by this workspace.")
        candidate = self._root.joinpath(*parts)
        try:
            resolved = candidate.resolve(strict=False)
            resolved.relative_to(self._root)
        except ValueError as exc:
            raise ValueError("The snapshot location is outside this workspace.") from exc
        return resolved

    def copy_source_to_snapshot(self, source_location: str, snapshot_location: str) -> Path:
        source = self.resolve_source_location(source_location)
        destination = self.resolve_analysis_snapshot_location(snapshot_location)
        if not source.is_dir() or source.is_symlink():
            raise ValueError("The captured source is not available.")
        if destination.exists():
            raise ValueError("The analysis snapshot already exists.")
        shutil.copytree(source, destination, symlinks=False, copy_function=shutil.copy2)
        return destination

    def cleanup_stale_staging_directories(
        self, retention: timedelta, *, now: datetime | None = None
    ) -> list[Path]:
        return self._cleanup_stale_direct_children(self._root / "staging", retention, now=now)

    def cleanup_stale_unreferenced_source_directories(
        self,
        current_source_locations: Iterable[str],
        retention: timedelta,
        *,
        now: datetime | None = None,
    ) -> list[str]:
        _validate_retention(retention)
        referenced = {
            "/".join(self._source_location_parts(location))
            for location in current_source_locations
        }
        cutoff = _cutoff(retention, now)
        removed: list[str] = []
        projects_root = self._root / "projects"
        if not projects_root.is_dir() or projects_root.is_symlink():
            return removed

        for project_directory in projects_root.iterdir():
            if not project_directory.is_dir() or project_directory.is_symlink():
                continue
            sources_root = project_directory / "sources"
            if not sources_root.is_dir() or sources_root.is_symlink():
                continue
            for source_directory in sources_root.iterdir():
                if not source_directory.is_dir() or source_directory.is_symlink():
                    continue
                location = source_directory.relative_to(self._root).as_posix()
                if location in referenced or source_directory.stat().st_mtime >= cutoff:
                    continue
                shutil.rmtree(source_directory)
                removed.append(location)
        return removed

    def _cleanup_stale_direct_children(
        self, parent: Path, retention: timedelta, *, now: datetime | None
    ) -> list[Path]:
        _validate_retention(retention)
        if not parent.is_dir() or parent.is_symlink():
            return []
        cutoff = _cutoff(retention, now)
        removed: list[Path] = []
        for child in parent.iterdir():
            if not child.is_dir() or child.is_symlink() or child.stat().st_mtime >= cutoff:
                continue
            shutil.rmtree(child)
            removed.append(child)
        return removed

    def _direct_child(self, candidate: Path, parent: Path) -> Path | None:
        try:
            resolved_parent = parent.resolve(strict=True)
            resolved_candidate = candidate.resolve(strict=False)
            if resolved_candidate.parent != resolved_parent:
                return None
            return resolved_candidate
        except FileNotFoundError:
            return None

    @staticmethod
    def _source_location(project_id: int, source_id: str) -> str:
        return f"projects/{project_id}/sources/{source_id}"

    @staticmethod
    def _source_location_parts(source_location: str) -> tuple[str, str, str, str]:
        path = PurePosixPath(source_location)
        parts = path.parts
        if (
            path.is_absolute()
            or len(parts) != 4
            or parts[0] != "projects"
            or parts[2] != "sources"
            or not parts[1].isdigit()
            or len(parts[3]) != 32
            or any(character not in "0123456789abcdef" for character in parts[3])
        ):
            raise ValueError("The source location is not a managed opaque location.")
        return parts  # type: ignore[return-value]


def _validate_project_id(project_id: int) -> int:
    if isinstance(project_id, bool) or not isinstance(project_id, int) or project_id <= 0:
        raise ValueError("The project id must be a positive integer.")
    return project_id


def _validate_retention(retention: timedelta) -> None:
    if retention.total_seconds() < 0:
        raise ValueError("The retention period must not be negative.")


def _cutoff(retention: timedelta, now: datetime | None) -> float:
    reference_time = now or datetime.now(timezone.utc)
    if reference_time.tzinfo is None:
        raise ValueError("The reference time must be timezone-aware.")
    return (reference_time - retention).timestamp()
