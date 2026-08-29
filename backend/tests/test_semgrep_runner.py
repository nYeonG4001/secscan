import subprocess
from pathlib import Path

import pytest

from app.services.semgrep_runner import (
    SemgrepRunError,
    SemgrepRunner,
    _is_resource_limit_exit,
    collect_analysis_targets,
    sanitize_execution_log,
)


def test_collect_analysis_targets_only_includes_supported_regular_source_files(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "App.java").write_text("class App {}")
    (tmp_path / "src" / "app.js").write_text("eval(code)")
    (tmp_path / "src" / "main.py").write_text("pass")
    (tmp_path / "src" / "ignored.ts").write_text("export {}")
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "bad.js").write_text("eval(code)")
    (tmp_path / "README.md").write_text("documentation")
    (tmp_path / "src" / "link.py").symlink_to(tmp_path / "src" / "main.py")

    assert collect_analysis_targets(tmp_path) == ["src/App.java", "src/app.js", "src/main.py"]


def test_execution_log_scrubs_paths_environment_and_archive_name(monkeypatch, tmp_path):
    monkeypatch.setenv("SECSCAN_TEST_SECRET", "sensitive-value")
    text = f"{tmp_path}/analyses/1/source upload.zip sensitive-value /private/command"

    sanitized = sanitize_execution_log(text, Path(tmp_path))

    assert sanitized is not None
    assert str(tmp_path) not in sanitized
    assert "upload.zip" not in sanitized
    assert "sensitive-value" not in sanitized
    assert "/private/command" not in sanitized


def test_runner_uses_wrapper_argument_array_and_safe_process_options(monkeypatch, tmp_path):
    (tmp_path / "main.py").write_text("print('safe')")
    rules = tmp_path / "rules.yml"
    rules.write_text("rules: []")
    captured: dict[str, object] = {}

    class Process:
        returncode = 0

        def communicate(self, timeout):
            captured["timeout"] = timeout
            return ('{"results": []}', "")

    def fake_popen(command, **kwargs):
        captured["command"] = command
        captured["kwargs"] = kwargs
        return Process()

    monkeypatch.setattr("app.services.semgrep_runner.subprocess.Popen", fake_popen)

    result = SemgrepRunner(
        executable="semgrep", rules_path=rules, timeout_seconds=7, cpu_limit_seconds=6
    ).run(tmp_path)

    command = captured["command"]
    assert isinstance(command, list)
    assert "--oss-only" in command
    assert "--json" in command
    assert "--quiet" in command
    assert "--config" in command
    assert "--no-rewrite-rule-ids" in command
    assert command[-1] == "main.py"
    kwargs = captured["kwargs"]
    assert kwargs["start_new_session"] is True
    assert kwargs.get("shell", False) is False
    assert "preexec_fn" not in kwargs
    assert result.metadata["result_count"] == 0


def test_runner_timeout_terminates_the_process_group(monkeypatch, tmp_path):
    (tmp_path / "main.py").write_text("print('safe')")
    rules = tmp_path / "rules.yml"
    rules.write_text("rules: []")
    killed: list[tuple[int, int]] = []

    class Process:
        pid = 31415
        returncode = -9
        calls = 0

        def communicate(self, timeout):
            self.calls += 1
            if self.calls == 1:
                raise subprocess.TimeoutExpired("semgrep", timeout)
            return "", "timeout /private/secscan/source.zip"

    monkeypatch.setattr(
        "app.services.semgrep_runner.subprocess.Popen", lambda *args, **kwargs: Process()
    )
    monkeypatch.setattr(
        "app.services.semgrep_runner.os.killpg", lambda pid, sig: killed.append((pid, sig))
    )

    with pytest.raises(SemgrepRunError, match="제한") as exc_info:
        SemgrepRunner(executable="semgrep", rules_path=rules, timeout_seconds=1).run(tmp_path)

    assert exc_info.value.error_code == "ANALYSIS_TIMEOUT"
    assert killed and killed[0][0] == 31415
    assert "/private" not in (exc_info.value.execution_log or "")
    assert "source.zip" not in (exc_info.value.execution_log or "")


def test_resource_limit_exit_mapping():
    assert _is_resource_limit_exit(-9, "")
    assert _is_resource_limit_exit(1, "out of memory")
    assert not _is_resource_limit_exit(1, "ordinary engine error")
