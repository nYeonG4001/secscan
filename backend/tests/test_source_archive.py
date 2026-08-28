import io
import stat
import zipfile

import pytest

from app.services.source_archive import (
    NoSupportedSourceError,
    SourceArchiveExtraction,
    SourceArchiveLimitExceededError,
    SourceArchiveLimits,
    SourceArchiveTooLargeError,
    UnsafeSourceArchiveError,
    extract_source_archive,
)


def make_archive(entries, *, compression=zipfile.ZIP_DEFLATED) -> io.BytesIO:
    archive_bytes = io.BytesIO()
    with zipfile.ZipFile(archive_bytes, "w", compression=compression) as archive:
        for name, content in entries:
            archive.writestr(name, content)
    archive_bytes.seek(0)
    return archive_bytes


def test_extracts_safe_archive_and_detects_supported_languages(tmp_path):
    archive = make_archive(
        [
            ("src/Main.java", "class Main {}"),
            ("web/app.mjs", "export {}"),
            ("scripts/check.py", "print('ok')"),
            ("README.md", "Documentation"),
            ("archive.zip", b"not extracted"),
        ]
    )
    staging = tmp_path / "staging"
    staging.mkdir()

    result = extract_source_archive(archive, staging)

    assert result == SourceArchiveExtraction(
        languages=("JAVA", "JAVASCRIPT", "PYTHON"), entry_count=5, extracted_bytes=59
    )
    assert (staging / "src/Main.java").read_text() == "class Main {}"
    assert (staging / "archive.zip").read_bytes() == b"not extracted"


@pytest.mark.parametrize(
    "entry_name",
    [
        "../escape.py",
        "/absolute.py",
        "C:/drive.py",
        "//server/share.py",
        "dir\\windows.py",
    ],
)
def test_rejects_unsafe_paths_before_extracting(tmp_path, entry_name):
    archive = make_archive([(entry_name, "print('unsafe')"), ("safe.py", "print('safe')")])
    staging = tmp_path / "staging"
    staging.mkdir()

    with pytest.raises(UnsafeSourceArchiveError):
        extract_source_archive(archive, staging)

    assert list(staging.iterdir()) == []


@pytest.mark.parametrize(
    "entries",
    [
        [("same.py", "one"), ("same.py", "two")],
        [("Code.py", "one"), ("code.py", "two")],
        [("file.py", "one"), ("file.py/child.py", "two")],
    ],
)
def test_rejects_duplicate_and_conflicting_paths_before_extracting(tmp_path, entries):
    archive = make_archive(entries)
    staging = tmp_path / "staging"
    staging.mkdir()

    with pytest.raises(UnsafeSourceArchiveError):
        extract_source_archive(archive, staging)

    assert list(staging.iterdir()) == []


def test_rejects_link_entries_before_extracting(tmp_path):
    archive_bytes = io.BytesIO()
    link = zipfile.ZipInfo("linked.py")
    link.create_system = 3
    link.external_attr = (stat.S_IFLNK | 0o777) << 16
    with zipfile.ZipFile(archive_bytes, "w") as archive:
        archive.writestr(link, "target.py")
        archive.writestr("safe.py", "print('safe')")
    archive_bytes.seek(0)
    staging = tmp_path / "staging"
    staging.mkdir()

    with pytest.raises(UnsafeSourceArchiveError):
        extract_source_archive(archive_bytes, staging)

    assert list(staging.iterdir()) == []


def test_rejects_nul_bytes_in_raw_archive_entry_name(tmp_path):
    archive = make_archive([("safe.py", "print('safe')")])
    archive_bytes = archive.getvalue().replace(b"safe.py", b"a.py\x00xx")
    staging = tmp_path / "staging"
    staging.mkdir()

    with pytest.raises(UnsafeSourceArchiveError):
        extract_source_archive(io.BytesIO(archive_bytes), staging)

    assert list(staging.iterdir()) == []


def test_rejects_archive_without_supported_regular_source_file(tmp_path):
    archive = make_archive([("README.md", "only docs"), ("app.ts", "unsupported")])
    staging = tmp_path / "staging"
    staging.mkdir()

    with pytest.raises(NoSupportedSourceError):
        extract_source_archive(archive, staging)

    assert list(staging.iterdir()) == []


def test_rejects_compressed_input_over_limit_before_extracting(tmp_path):
    archive = make_archive([("safe.py", "print('safe')")], compression=zipfile.ZIP_STORED)
    staging = tmp_path / "staging"
    staging.mkdir()

    with pytest.raises(SourceArchiveTooLargeError):
        extract_source_archive(archive, staging, limits=SourceArchiveLimits(max_input_bytes=10))

    assert list(staging.iterdir()) == []


def test_allows_high_expansion_ratio_before_output_threshold(tmp_path):
    archive = make_archive([("small.py", "a" * 99)])
    staging = tmp_path / "staging"
    staging.mkdir()
    limits = SourceArchiveLimits(
        max_expansion_ratio=2,
        ratio_check_output_bytes=100,
        chunk_size=8,
    )
    with zipfile.ZipFile(archive) as metadata:
        assert 99 / metadata.getinfo("small.py").compress_size > limits.max_expansion_ratio

    result = extract_source_archive(
        archive,
        staging,
        limits=limits,
    )

    assert result.extracted_bytes == 99
    assert (staging / "small.py").read_text() == "a" * 99


@pytest.mark.parametrize(
    "entries, limits",
    [
        (
            [("one.py", "1"), ("two.py", "2")],
            SourceArchiveLimits(max_entries=1),
        ),
        (
            [("large.py", "12345")],
            SourceArchiveLimits(max_file_bytes=4),
        ),
        (
            [("one.py", "1234"), ("two.py", "5678")],
            SourceArchiveLimits(max_extracted_bytes=6),
        ),
        (
            [("repeated.py", "a" * 1_000)],
            SourceArchiveLimits(
                max_expansion_ratio=2,
                ratio_check_output_bytes=8,
                chunk_size=8,
            ),
        ),
    ],
)
def test_enforces_streaming_extraction_limits(tmp_path, entries, limits):
    archive = make_archive(entries)
    staging = tmp_path / "staging"
    staging.mkdir()

    with pytest.raises(SourceArchiveLimitExceededError):
        extract_source_archive(archive, staging, limits=limits)
