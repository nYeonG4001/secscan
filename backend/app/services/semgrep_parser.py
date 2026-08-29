"""Semgrep JSON을 저장소 독립적인 내부 Finding으로 변환한다."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any


class SemgrepOutputInvalid(ValueError):
    """하나라도 저장할 수 없는 Semgrep 결과가 있을 때 발생한다."""


@dataclass(frozen=True)
class NormalizedFinding:
    engine_rule_id: str
    rule_name: str
    severity: str | None
    confidence: str
    language: str | None
    file_path: str
    line: int | None
    end_line: int | None
    message: str
    evidence: str
    raw_result: dict[str, Any]


def parse_semgrep_results(results: object, snapshot_root: Path) -> list[NormalizedFinding]:
    if not isinstance(results, list):
        raise SemgrepOutputInvalid("results must be a list")
    return [parse_semgrep_result(result, snapshot_root) for result in results]


def parse_semgrep_result(result: object, snapshot_root: Path) -> NormalizedFinding:
    if not isinstance(result, dict):
        raise SemgrepOutputInvalid("result must be an object")
    check_id = _required_string(result, "check_id")
    file_path = _relative_path(_required_string(result, "path"), snapshot_root)
    start = _required_object(result, "start")
    end = _required_object(result, "end")
    line = _positive_line(start, "line")
    end_line = _positive_line(end, "line")
    if end_line < line:
        raise SemgrepOutputInvalid("end line precedes start line")
    extra = _required_object(result, "extra")
    message = _required_string(extra, "message")
    metadata = extra.get("metadata", {})
    if not isinstance(metadata, dict):
        raise SemgrepOutputInvalid("extra.metadata must be an object")
    basis = metadata.get("secscan_basis")
    if basis is not None and not isinstance(basis, str):
        raise SemgrepOutputInvalid("secscan_basis must be a string")
    confidence = _normalize_confidence(metadata.get("confidence"))
    language = metadata.get("language") or _language_from_path(file_path)
    if language is not None and not isinstance(language, str):
        raise SemgrepOutputInvalid("metadata.language must be a string")
    severity = extra.get("severity")
    if severity is not None and not isinstance(severity, str):
        raise SemgrepOutputInvalid("extra.severity must be a string")
    rule_name = metadata.get("title", check_id)
    if not isinstance(rule_name, str) or not rule_name.strip():
        raise SemgrepOutputInvalid("metadata.title must be a non-empty string")
    evidence = (
        basis[: 2 * 1024]
        if basis
        else _fallback_evidence(check_id, file_path, line, end_line)
    )
    raw_result = dict(result)
    raw_result["path"] = file_path
    return NormalizedFinding(
        engine_rule_id=check_id,
        rule_name=rule_name,
        severity=severity,
        confidence=confidence,
        language=language,
        file_path=file_path,
        line=line,
        end_line=end_line,
        message=message,
        evidence=evidence,
        raw_result=raw_result,
    )


def _required_object(value: dict[str, Any], key: str) -> dict[str, Any]:
    field = value.get(key)
    if not isinstance(field, dict):
        raise SemgrepOutputInvalid(f"{key} must be an object")
    return field


def _required_string(value: dict[str, Any], key: str) -> str:
    field = value.get(key)
    if not isinstance(field, str) or not field.strip():
        raise SemgrepOutputInvalid(f"{key} must be a non-empty string")
    return field


def _positive_line(value: dict[str, Any], key: str) -> int:
    field = value.get(key)
    if isinstance(field, bool) or not isinstance(field, int) or field < 1:
        raise SemgrepOutputInvalid(f"{key} must be a positive integer")
    return field


def _relative_path(value: str, snapshot_root: Path) -> str:
    path = Path(value)
    root = snapshot_root.resolve(strict=True)
    if path.is_absolute():
        try:
            resolved = path.resolve(strict=False)
            relative = resolved.relative_to(root)
        except ValueError as exc:
            raise SemgrepOutputInvalid("path is outside snapshot root") from exc
    else:
        pure = PurePosixPath(value)
        if not value or pure.is_absolute() or ".." in pure.parts:
            raise SemgrepOutputInvalid("path is not a safe relative path")
        relative = pure
    normalized = PurePosixPath(relative).as_posix()
    if normalized in {"", "."}:
        raise SemgrepOutputInvalid("path is empty")
    return normalized


def _normalize_confidence(value: object) -> str:
    if not isinstance(value, str):
        return "UNKNOWN"
    return value.upper() if value.upper() in {"HIGH", "MEDIUM", "LOW"} else "UNKNOWN"


def _fallback_evidence(rule_id: str, file_path: str, line: int, end_line: int) -> str:
    location = f"{file_path}:{line}" if end_line == line else f"{file_path}:{line}-{end_line}"
    return f"Semgrep rule {rule_id} reported {location}."


def _language_from_path(file_path: str) -> str | None:
    language_by_suffix = {
        ".java": "JAVA",
        ".js": "JAVASCRIPT",
        ".jsx": "JAVASCRIPT",
        ".mjs": "JAVASCRIPT",
        ".cjs": "JAVASCRIPT",
        ".py": "PYTHON",
    }
    return language_by_suffix.get(Path(file_path).suffix.lower())
