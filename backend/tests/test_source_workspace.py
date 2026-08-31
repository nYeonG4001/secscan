import io
import os
import zipfile
from datetime import datetime, timedelta, timezone

import pytest

from app.services.project_upload_lock import ProjectUploadLocks, UploadInProgressError
from app.services.source_archive import UnsafeSourceArchiveError, extract_source_archive
from app.services.source_workspace import SourceWorkspace


def test_staging_context_cleans_up_after_exception_and_cancellation(tmp_path):
    workspace = SourceWorkspace(tmp_path / "storage")
    with pytest.raises(RuntimeError):
        with workspace.staging_directory() as staging:
            (staging / "partial.py").write_text("partial")
            raise RuntimeError("cancelled")

    assert list((tmp_path / "storage/staging").iterdir()) == []


def test_staging_context_cleans_up_after_archive_rejection(tmp_path):
    workspace = SourceWorkspace(tmp_path / "storage")
    archive = io.BytesIO()
    with zipfile.ZipFile(archive, "w") as output:
        output.writestr("../unsafe.py", "unsafe")
    archive.seek(0)

    with pytest.raises(UnsafeSourceArchiveError):
        with workspace.staging_directory() as staging:
            extract_source_archive(archive, staging)

    assert list((tmp_path / "storage/staging").iterdir()) == []


def test_promote_creates_opaque_source_location_without_replacing_existing_source(tmp_path):
    workspace = SourceWorkspace(tmp_path / "storage")
    with workspace.staging_directory() as first_staging:
        (first_staging / "first.py").write_text("first")
        first_location = workspace.promote_staging_directory(42, first_staging)
    with workspace.staging_directory() as second_staging:
        (second_staging / "second.py").write_text("second")
        second_location = workspace.promote_staging_directory(42, second_staging)

    first_path = workspace.resolve_source_location(first_location)
    second_path = workspace.resolve_source_location(second_location)
    assert first_location.startswith("projects/42/sources/")
    assert first_location != second_location
    assert (first_path / "first.py").read_text() == "first"
    assert (second_path / "second.py").read_text() == "second"


def test_cleanup_removes_only_stale_unreferenced_staging_and_sources(tmp_path):
    workspace = SourceWorkspace(tmp_path / "storage")
    with workspace.staging_directory() as kept_staging:
        (kept_staging / "keep.py").write_text("keep")
        kept_location = workspace.promote_staging_directory(7, kept_staging)
    with workspace.staging_directory() as stale_staging:
        (stale_staging / "stale.py").write_text("stale")
        stale_location = workspace.promote_staging_directory(7, stale_staging)
    fresh_staging = workspace.create_staging_directory()
    stale_staging = workspace.create_staging_directory()

    old_time = (datetime.now(timezone.utc) - timedelta(days=2)).timestamp()
    os.utime(workspace.resolve_source_location(stale_location), (old_time, old_time))
    os.utime(stale_staging, (old_time, old_time))

    removed_staging = workspace.cleanup_stale_staging_directories(timedelta(days=1))
    removed_sources = workspace.cleanup_stale_unreferenced_source_directories(
        [kept_location], timedelta(days=1)
    )

    assert removed_staging == [stale_staging]
    assert removed_sources == [stale_location]
    assert workspace.resolve_source_location(kept_location).is_dir()
    assert not workspace.resolve_source_location(stale_location).exists()
    assert fresh_staging.is_dir()


def test_cleanup_ignores_unmanaged_current_source_locations(tmp_path):
    workspace = SourceWorkspace(tmp_path / "storage")
    with workspace.staging_directory() as kept_staging:
        (kept_staging / "keep.py").write_text("keep")
        kept_location = workspace.promote_staging_directory(7, kept_staging)
    with workspace.staging_directory() as stale_staging:
        (stale_staging / "stale.py").write_text("stale")
        stale_location = workspace.promote_staging_directory(7, stale_staging)

    old_time = (datetime.now(timezone.utc) - timedelta(days=2)).timestamp()
    os.utime(workspace.resolve_source_location(stale_location), (old_time, old_time))

    removed_sources = workspace.cleanup_stale_unreferenced_source_directories(
        [kept_location, "/legacy/current-source"], timedelta(days=1)
    )

    assert removed_sources == [stale_location]
    assert workspace.resolve_source_location(kept_location).is_dir()
    assert not workspace.resolve_source_location(stale_location).exists()
    assert not workspace.is_managed_source_location("/legacy/current-source")


def test_workspace_rejects_unmanaged_staging_and_source_locations(tmp_path):
    workspace = SourceWorkspace(tmp_path / "storage")
    unmanaged = tmp_path / "unmanaged"
    unmanaged.mkdir()

    with pytest.raises(ValueError):
        workspace.promote_staging_directory(1, unmanaged)
    with pytest.raises(ValueError):
        workspace.resolve_source_location("../../outside")


def test_project_upload_lock_rejects_concurrent_acquisition_and_releases_after_error():
    locks = ProjectUploadLocks()

    with locks.acquire(3):
        assert locks.is_locked(3)
        with pytest.raises(UploadInProgressError):
            with locks.acquire(3):
                pass

    assert not locks.is_locked(3)
    with pytest.raises(RuntimeError):
        with locks.acquire(3):
            raise RuntimeError("failed upload")
    assert not locks.is_locked(3)
