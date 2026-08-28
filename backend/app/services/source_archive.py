from __future__ import annotations

import io
import stat
import struct
import unicodedata
import zipfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import BinaryIO

MEBIBYTE = 1024 * 1024
_LANGUAGE_EXTENSIONS = {
    ".java": "JAVA",
    ".js": "JAVASCRIPT",
    ".jsx": "JAVASCRIPT",
    ".mjs": "JAVASCRIPT",
    ".cjs": "JAVASCRIPT",
    ".py": "PYTHON",
}
_LANGUAGE_ORDER = ("JAVA", "JAVASCRIPT", "PYTHON")
_SUPPORTED_COMPRESSION_TYPES = {
    zipfile.ZIP_STORED,
    zipfile.ZIP_DEFLATED,
    zipfile.ZIP_BZIP2,
    zipfile.ZIP_LZMA,
}
_CENTRAL_DIRECTORY_HEADER = struct.Struct("<4s6H3L5H2L")
_CENTRAL_DIRECTORY_SIGNATURE = b"PK\x01\x02"


class SourceArchiveError(Exception):
    """외부에는 범주만 안전하게 노출할 수 있는 압축 파일 오류의 기본 예외다."""


class InvalidSourceArchiveError(SourceArchiveError):
    """입력이 읽을 수 있는 ZIP 파일이 아니다."""


class UnsafeSourceArchiveError(SourceArchiveError):
    """압축 해제에 안전하지 않은 항목이 있다."""


class SourceArchiveTooLargeError(SourceArchiveError):
    """압축된 ZIP 입력이 설정된 제한을 초과했다."""


class SourceArchiveLimitExceededError(SourceArchiveError):
    """스트리밍 압축 해제가 출력 관련 자원 제한을 초과했다."""


class NoSupportedSourceError(SourceArchiveError):
    """압축 파일에 지원되는 일반 소스 파일이 없다."""


@dataclass(frozen=True)
class SourceArchiveLimits:
    max_input_bytes: int = 25 * MEBIBYTE
    max_extracted_bytes: int = 100 * MEBIBYTE
    max_entries: int = 5_000
    max_file_bytes: int = 10 * MEBIBYTE
    max_expansion_ratio: float = 20.0
    ratio_check_output_bytes: int = MEBIBYTE
    chunk_size: int = 64 * 1024

    def __post_init__(self) -> None:
        positive_values = (
            self.max_input_bytes,
            self.max_extracted_bytes,
            self.max_entries,
            self.max_file_bytes,
            self.ratio_check_output_bytes,
            self.chunk_size,
        )
        if any(value <= 0 for value in positive_values) or self.max_expansion_ratio <= 0:
            raise ValueError("Archive limits must be greater than zero.")


@dataclass(frozen=True)
class SourceArchiveExtraction:
    languages: tuple[str, ...]
    entry_count: int
    extracted_bytes: int


@dataclass(frozen=True)
class _ValidatedEntry:
    info: zipfile.ZipInfo
    relative_path: PurePosixPath
    is_directory: bool


class _CountingReader:
    """ZIP 스트림에서 실제로 읽은 바이트를 세는 seek 가능 리더 래퍼다."""

    def __init__(self, source: BinaryIO) -> None:
        self._source = source
        self.bytes_read = 0

    def read(self, size: int = -1) -> bytes:
        data = self._source.read(size)
        self.bytes_read += len(data)
        return data

    def seek(self, offset: int, whence: int = io.SEEK_SET) -> int:
        return self._source.seek(offset, whence)

    def tell(self) -> int:
        return self._source.tell()

    def seekable(self) -> bool:
        return self._source.seekable()

    def readable(self) -> bool:
        return self._source.readable()


def extract_source_archive(
    archive_input: BinaryIO,
    staging_directory: Path,
    *,
    limits: SourceArchiveLimits | None = None,
) -> SourceArchiveExtraction:
    """ZIP 전체를 검증한 뒤 빈 staging 디렉터리에 스트리밍 방식으로 압축 해제한다."""
    effective_limits = limits or SourceArchiveLimits()
    staging_root = _require_empty_staging_directory(staging_directory)
    _check_input_size(archive_input, effective_limits)
    reader = _CountingReader(archive_input)

    try:
        with zipfile.ZipFile(reader) as archive:
            _validate_raw_entry_names(archive_input, archive)
            entries = _validate_entries(archive, effective_limits)
            languages = _detect_languages(entries)
            if not languages:
                raise NoSupportedSourceError()
            extracted_bytes = _extract_entries(
                archive, reader, entries, staging_root, effective_limits
            )
    except SourceArchiveError:
        raise
    except (NotImplementedError, zipfile.BadZipFile, zipfile.LargeZipFile) as exc:
        raise InvalidSourceArchiveError() from exc

    return SourceArchiveExtraction(
        languages=languages,
        entry_count=len(entries),
        extracted_bytes=extracted_bytes,
    )


def _require_empty_staging_directory(staging_directory: Path) -> Path:
    try:
        root = staging_directory.resolve(strict=True)
    except FileNotFoundError as exc:
        raise ValueError("The staging directory must already exist.") from exc
    if not root.is_dir() or root.is_symlink():
        raise ValueError("The staging directory must be a real directory.")
    if any(root.iterdir()):
        raise ValueError("The staging directory must be empty.")
    return root


def _check_input_size(archive_input: BinaryIO, limits: SourceArchiveLimits) -> None:
    try:
        archive_input.seek(0, io.SEEK_END)
        input_size = archive_input.tell()
        archive_input.seek(0)
    except (AttributeError, OSError) as exc:
        raise ValueError("The ZIP input must be a seekable binary stream.") from exc
    if input_size > limits.max_input_bytes:
        raise SourceArchiveTooLargeError()


def _validate_entries(
    archive: zipfile.ZipFile, limits: SourceArchiveLimits
) -> list[_ValidatedEntry]:
    entries = archive.infolist()
    if len(entries) > limits.max_entries:
        raise SourceArchiveLimitExceededError()

    validated: list[_ValidatedEntry] = []
    exact_paths: set[str] = set()
    casefolded_paths: set[str] = set()
    regular_paths: set[PurePosixPath] = set()
    for info in entries:
        relative_path = _validate_entry_path(info.filename)
        is_directory = info.is_dir()
        _validate_entry_type(info, is_directory)
        normalized_path = relative_path.as_posix()
        casefolded_path = normalized_path.casefold()
        if normalized_path in exact_paths or casefolded_path in casefolded_paths:
            raise UnsafeSourceArchiveError()
        exact_paths.add(normalized_path)
        casefolded_paths.add(casefolded_path)
        if not is_directory:
            regular_paths.add(relative_path)
        validated.append(_ValidatedEntry(info, relative_path, is_directory))

    for regular_path in regular_paths:
        if any(
            parent in regular_paths
            for parent in regular_path.parents
            if parent != PurePosixPath(".")
        ):
            raise UnsafeSourceArchiveError()
    return validated


def _validate_raw_entry_names(archive_input: BinaryIO, archive: zipfile.ZipFile) -> None:
    try:
        archive_input.seek(archive.start_dir)
        for _ in archive.infolist():
            header = archive_input.read(_CENTRAL_DIRECTORY_HEADER.size)
            if len(header) != _CENTRAL_DIRECTORY_HEADER.size:
                raise InvalidSourceArchiveError()
            fields = _CENTRAL_DIRECTORY_HEADER.unpack(header)
            if fields[0] != _CENTRAL_DIRECTORY_SIGNATURE:
                raise InvalidSourceArchiveError()
            filename_length, extra_length, comment_length = fields[10:13]
            filename = archive_input.read(filename_length)
            if len(filename) != filename_length:
                raise InvalidSourceArchiveError()
            if b"\x00" in filename:
                raise UnsafeSourceArchiveError()
            archive_input.seek(extra_length + comment_length, io.SEEK_CUR)
    except SourceArchiveError:
        raise
    except (AttributeError, OSError, struct.error) as exc:
        raise InvalidSourceArchiveError() from exc


def _validate_entry_path(filename: str) -> PurePosixPath:
    if "\x00" in filename or "\\" in filename:
        raise UnsafeSourceArchiveError()
    if filename.startswith("/") or filename.startswith("//"):
        raise UnsafeSourceArchiveError()
    if len(filename) >= 2 and filename[0].isalpha() and filename[1] == ":":
        raise UnsafeSourceArchiveError()

    components: list[str] = []
    for component in filename.split("/"):
        if component in ("", "."):
            continue
        if component == "..":
            raise UnsafeSourceArchiveError()
        components.append(unicodedata.normalize("NFC", component))
    if not components:
        raise UnsafeSourceArchiveError()
    return PurePosixPath(*components)


def _validate_entry_type(info: zipfile.ZipInfo, is_directory: bool) -> None:
    if info.flag_bits & 0x1 or info.compress_type not in _SUPPORTED_COMPRESSION_TYPES:
        raise UnsafeSourceArchiveError()

    mode = info.external_attr >> 16
    file_type = stat.S_IFMT(mode)
    if file_type and file_type not in (stat.S_IFREG, stat.S_IFDIR):
        raise UnsafeSourceArchiveError()
    if is_directory and file_type == stat.S_IFREG:
        raise UnsafeSourceArchiveError()
    if not is_directory and file_type == stat.S_IFDIR:
        raise UnsafeSourceArchiveError()


def _detect_languages(entries: list[_ValidatedEntry]) -> tuple[str, ...]:
    languages = {
        _LANGUAGE_EXTENSIONS.get(entry.relative_path.suffix.lower())
        for entry in entries
        if not entry.is_directory
    }
    return tuple(language for language in _LANGUAGE_ORDER if language in languages)


def _extract_entries(
    archive: zipfile.ZipFile,
    reader: _CountingReader,
    entries: list[_ValidatedEntry],
    staging_root: Path,
    limits: SourceArchiveLimits,
) -> int:
    total_output = 0
    for entry in entries:
        destination = _destination_in_staging(staging_root, entry.relative_path)
        if entry.is_directory:
            destination.mkdir(parents=True, exist_ok=True)
            continue

        destination.parent.mkdir(parents=True, exist_ok=True)
        _ensure_destination_in_staging(staging_root, destination)
        with archive.open(entry.info) as source, destination.open("xb") as target:
            compressed_start = reader.bytes_read
            file_output = 0
            while chunk := source.read(limits.chunk_size):
                file_output += len(chunk)
                total_output += len(chunk)
                if file_output > limits.max_file_bytes or total_output > limits.max_extracted_bytes:
                    raise SourceArchiveLimitExceededError()
                compressed_input = reader.bytes_read - compressed_start
                if (
                    file_output >= limits.ratio_check_output_bytes
                    and compressed_input > 0
                    and file_output / compressed_input > limits.max_expansion_ratio
                ):
                    raise SourceArchiveLimitExceededError()
                _ensure_destination_in_staging(staging_root, destination)
                target.write(chunk)
    return total_output


def _destination_in_staging(staging_root: Path, relative_path: PurePosixPath) -> Path:
    destination = staging_root.joinpath(*relative_path.parts)
    _ensure_destination_in_staging(staging_root, destination)
    return destination


def _ensure_destination_in_staging(staging_root: Path, destination: Path) -> None:
    try:
        destination.resolve(strict=False).relative_to(staging_root)
    except ValueError as exc:
        raise UnsafeSourceArchiveError() from exc
