"""Safe, local Semgrep execution for E4.

Only this module constructs the subprocess argument list. It deliberately does
not normalize or persist Semgrep findings; E5 owns that boundary.
"""

from __future__ import annotations

import json
import os
import re
import signal
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from app.core.config import settings

EXCLUDED_DIRECTORIES = {
    "node_modules",
    "vendor",
    "dist",
    "build",
    "target",
    ".venv",
    "venv",
    "__pycache__",
}
SUPPORTED_SUFFIXES = {".java", ".js", ".jsx", ".mjs", ".cjs", ".py"}
LOG_LIMIT_BYTES = 64 * 1024
TERMINATION_GRACE_SECONDS = 3


@dataclass(frozen=True)
class SemgrepRunResult:
    result_count: int
    results: list[dict]
    metadata: dict[str, object]
    execution_log: str | None


class SemgrepRunError(Exception):
    def __init__(self, error_code: str, message: str, execution_log: str | None = None) -> None:
        super().__init__(message)
        self.error_code = error_code
        self.message = message
        self.execution_log = execution_log


def rule_file() -> Path:
    return Path(__file__).resolve().parents[2] / "semgrep-rules" / "secscan-security.yml"


def collect_analysis_targets(snapshot_root: Path) -> list[str]:
    """Return snapshot-relative regular files in a stable order."""
    root = snapshot_root.resolve(strict=True)
    targets: list[str] = []
    for candidate in root.rglob("*"):
        relative = candidate.relative_to(root)
        if any(part in EXCLUDED_DIRECTORIES for part in relative.parts):
            continue
        if (
            candidate.is_symlink()
            or not candidate.is_file()
            or candidate.suffix not in SUPPORTED_SUFFIXES
        ):
            continue
        targets.append(relative.as_posix())
    return sorted(targets)


class SemgrepRunner:
    def __init__(
        self,
        *,
        executable: str | None = None,
        cli_version: str | None = None,
        rules_path: Path | None = None,
        timeout_seconds: int | None = None,
        cpu_limit_seconds: int | None = None,
        address_space_limit_bytes: int | None = None,
    ) -> None:
        self.executable = executable or settings.SEMGREP_CLI_PATH
        self.cli_version = cli_version or settings.SEMGREP_CLI_VERSION
        self.rules_path = rules_path or rule_file()
        self.timeout_seconds = timeout_seconds or settings.SEMGREP_TIMEOUT_SECONDS
        self.cpu_limit_seconds = cpu_limit_seconds or settings.SEMGREP_CPU_LIMIT_SECONDS
        self.address_space_limit_bytes = (
            address_space_limit_bytes or settings.SEMGREP_ADDRESS_SPACE_LIMIT_BYTES
        )

    def run(self, snapshot_root: Path) -> SemgrepRunResult:
        targets = collect_analysis_targets(snapshot_root)
        if not targets:
            raise SemgrepRunError("ENGINE_EXECUTION_FAILED", "분석할 지원 소스 파일이 없습니다.")
        if not self.rules_path.is_file():
            raise SemgrepRunError("ENGINE_EXECUTION_FAILED", "분석 규칙을 사용할 수 없습니다.")

        command = [
            sys.executable,
            "-m",
            "app.services.semgrep_wrapper",
            "--memory-bytes",
            str(self.address_space_limit_bytes),
            "--cpu-seconds",
            str(self.cpu_limit_seconds),
            "--",
            self.executable,
            "--config",
            str(self.rules_path),
            "--no-rewrite-rule-ids",
            "--json",
            "--quiet",
            "--oss-only",
            "--metrics=off",
            *targets,
        ]
        environment = os.environ.copy()
        backend_root = str(Path(__file__).resolve().parents[2])
        environment["PYTHONPATH"] = os.pathsep.join(
            value for value in (backend_root, environment.get("PYTHONPATH")) if value
        )
        process = subprocess.Popen(
            command,
            cwd=snapshot_root,
            env=environment,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            start_new_session=True,
        )
        try:
            stdout, stderr = process.communicate(timeout=self.timeout_seconds)
        except subprocess.TimeoutExpired:
            stdout, stderr = self._terminate_process_group(process)
            raise SemgrepRunError(
                "ANALYSIS_TIMEOUT",
                "분석 실행 시간이 제한을 초과했습니다.",
                sanitize_execution_log(stderr, snapshot_root),
            )

        log = sanitize_execution_log(stderr, snapshot_root)
        if process.returncode != 0:
            if _is_resource_limit_exit(process.returncode, stderr):
                raise SemgrepRunError(
                    "ANALYSIS_RESOURCE_LIMIT",
                    "분석 실행이 자원 제한으로 종료되었습니다.",
                    log,
                )
            raise SemgrepRunError("ENGINE_EXECUTION_FAILED", "분석 엔진 실행에 실패했습니다.", log)

        try:
            output = json.loads(stdout)
            results = output["results"]
            if not isinstance(results, list):
                raise ValueError
        except (json.JSONDecodeError, KeyError, TypeError, ValueError):
            raise SemgrepRunError(
                "ENGINE_OUTPUT_INVALID",
                "분석 엔진 출력 형식이 올바르지 않습니다.",
                log,
            )
        metadata: dict[str, object] = {
            "engine": "semgrep",
            "cli_version": self.cli_version,
            "ruleset_id": "secscan-rules-2026-08-28",
            "output_format": "semgrep-json",
            "exit_code": process.returncode,
            "result_count": len(results),
        }
        return SemgrepRunResult(len(results), results, metadata, log)

    def _terminate_process_group(self, process: subprocess.Popen[str]) -> tuple[str, str]:
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        try:
            return process.communicate(timeout=TERMINATION_GRACE_SECONDS)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            return process.communicate()


def _is_resource_limit_exit(returncode: int, stderr: str) -> bool:
    resource_signals = {signal.SIGXCPU, signal.SIGKILL, signal.SIGSEGV}
    return (
        returncode < 0
        and -returncode in resource_signals
        or bool(re.search(r"(memory|resource|rlimit|out of memory)", stderr, re.IGNORECASE))
    )


def sanitize_execution_log(text: str, snapshot_root: Path | None = None) -> str | None:
    if not text:
        return None
    sanitized = text
    forbidden = [str(settings.STORAGE_ROOT)]
    if snapshot_root is not None:
        forbidden.append(str(snapshot_root))
    forbidden.extend(value for value in os.environ.values() if len(value) >= 5)
    for value in sorted(set(forbidden), key=len, reverse=True):
        sanitized = sanitized.replace(value, "[비공개]")
    sanitized = re.sub(r"(?:[A-Za-z]:[\\/]|/)[^\s'\"`]+", "[내부 경로]", sanitized)
    sanitized = re.sub(r"\b[^\s'\"`]+\.zip\b", "[업로드 파일]", sanitized, flags=re.IGNORECASE)
    encoded = sanitized.encode("utf-8")
    if len(encoded) > LOG_LIMIT_BYTES:
        sanitized = encoded[-LOG_LIMIT_BYTES:].decode("utf-8", errors="ignore")
    return sanitized
