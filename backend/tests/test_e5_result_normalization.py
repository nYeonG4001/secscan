import shutil
from pathlib import Path

import pytest
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError

from app.models.analysis import Analysis
from app.models.finding import Finding
from app.models.kisa_catalog import KisaCatalog
from app.models.kisa_rule_mapping import KisaRuleMapping
from app.models.project import Project
from app.models.user import User
from app.schemas.catalog import CatalogItemCreate, CatalogItemOut, CatalogItemUpdate
from app.schemas.finding import FindingAdminOut, FindingUserOut
from app.services.finding_normalizer import persist_normalized_findings
from app.services.kisa_catalog_seed import seed_kisa_catalog, seed_kisa_rule_mappings
from app.services.semgrep_parser import SemgrepOutputInvalid, parse_semgrep_results
from app.services.semgrep_runner import SemgrepRunner

FIXTURE_ROOT = Path(__file__).parent / "fixtures"


def _analysis(db_session):
    user = User(email="e5@secscan.io", password_hash="hash", role="ADMIN")
    db_session.add(user)
    db_session.flush()
    project = Project(name="E5", created_by=user.id, target_languages=["PYTHON"])
    db_session.add(project)
    db_session.flush()
    analysis = Analysis(project_id=project.id, executed_by=user.id, status="RUNNING")
    db_session.add(analysis)
    db_session.flush()
    return analysis


def _result(
    rule_id="unmapped.rule",
    path="sample.py",
    message="message",
    severity="WARNING",
):
    return {
        "check_id": rule_id,
        "path": path,
        "start": {"line": 3},
        "end": {"line": 3},
        "extra": {
            "message": message,
            "severity": severity,
            "metadata": {},
        },
    }


def test_unmapped_result_is_preserved_and_raw_is_admin_only(db_session, tmp_path):
    analysis = _analysis(db_session)
    (tmp_path / "sample.py").write_text("one\ntwo\nthree\nfour\nfive\n")
    normalized = parse_semgrep_results([_result()], tmp_path)
    persist_normalized_findings(db_session, analysis.id, tmp_path, normalized)
    db_session.commit()
    finding = db_session.query(Finding).one()
    assert (finding.kisa_code, finding.criterion_id, finding.recommendation) == (
        None,
        None,
        None,
    )
    assert finding.severity == "MEDIUM"
    assert FindingUserOut.model_validate(finding).model_dump().get("raw_result") is None
    assert FindingAdminOut.model_validate(finding).raw_result == finding.raw_result


def test_deduplicates_first_result_per_analysis_but_not_across_analyses(db_session, tmp_path):
    (tmp_path / "sample.py").write_text("a\nb\nc\n")
    first, second = _result(message="first"), _result(message="second")
    one = _analysis(db_session)
    persist_normalized_findings(
        db_session,
        one.id,
        tmp_path,
        parse_semgrep_results([first, second], tmp_path),
    )
    one.status = "COMPLETED"
    db_session.flush()
    two = Analysis(
        project_id=one.project_id,
        executed_by=one.executed_by,
        status="RUNNING",
    )
    db_session.add(two)
    db_session.flush()
    persist_normalized_findings(
        db_session,
        two.id,
        tmp_path,
        parse_semgrep_results([first], tmp_path),
    )
    db_session.commit()
    assert db_session.query(Finding).filter_by(analysis_id=one.id).one().message == "first"
    assert db_session.query(Finding).count() == 2


def test_mapping_constraints_and_seed_status(db_session):
    seed_kisa_catalog(db_session)
    seed_kisa_rule_mappings(db_session)
    # 이 집합은 현재 revision에서 검증된 매핑·부분 지원 상태이며 규칙 수 상한이 아니다.
    # 새 규칙이 fixture와 CI 게이트를 통과하면 해당 기대값을 함께 확장한다.
    partial_support_codes = {
        "KISA-001",
        "KISA-002",
        "KISA-003",
        "KISA-004",
        "KISA-005",
        "KISA-043",
    }
    assert {
        (mapping.engine_rule_id, mapping.kisa_code)
        for mapping in db_session.query(KisaRuleMapping).all()
    } == {
        ("secscan.java.runtime-exec", "KISA-005"),
        ("secscan.javascript.eval", "KISA-002"),
        ("secscan.python.pickle-loads", "KISA-043"),
        ("secscan.java.jdbc-statement-sql", "KISA-001"),
        ("secscan.javascript.dom-innerhtml", "KISA-004"),
        ("secscan.python.open-user-path", "KISA-003"),
        ("secscan.python.os-system", "KISA-005"),
        ("secscan.python.eval", "KISA-002"),
        ("secscan.python.exec", "KISA-002"),
        ("secscan.python.pickle-load", "KISA-043"),
        ("secscan.python.path-open", "KISA-003"),
        ("secscan.javascript.function-constructor", "KISA-002"),
        ("secscan.javascript.dom-insert-adjacent-html", "KISA-004"),
        ("secscan.java.process-builder", "KISA-005"),
        ("secscan.python.subprocess-run-shell", "KISA-005"),
        ("secscan.javascript.dom-outerhtml", "KISA-004"),
        ("secscan.javascript.document-write", "KISA-004"),
        ("secscan.python.pickle-unpickler-load", "KISA-043"),
        ("secscan.python.subprocess-popen-shell", "KISA-005"),
        ("secscan.python.subprocess-call-shell", "KISA-005"),
        ("secscan.python.subprocess-check-call-shell", "KISA-005"),
        ("secscan.python.subprocess-check-output-shell", "KISA-005"),
        ("secscan.python.os-popen", "KISA-005"),
        ("secscan.python.subprocess-output-shell", "KISA-005"),
    }
    catalog_items = db_session.query(KisaCatalog).all()
    assert {
        item.kisa_code for item in catalog_items if item.implementation_status == "부분 지원"
    } == partial_support_codes
    assert all(
        item.implementation_status == "미지원"
        for item in catalog_items
        if item.kisa_code not in partial_support_codes
    )
    db_session.add(KisaRuleMapping(engine="semgrep", engine_rule_id="extra", kisa_code="KISA-005"))
    db_session.commit()
    db_session.add(KisaRuleMapping(engine="semgrep", engine_rule_id="extra", kisa_code="KISA-002"))
    with pytest.raises(IntegrityError):
        db_session.commit()


def test_mapped_result_uses_catalog_snapshots_and_relative_raw_path(db_session, tmp_path):
    seed_kisa_catalog(db_session)
    seed_kisa_rule_mappings(db_session)
    catalog = db_session.get(KisaCatalog, "KISA-002")
    catalog.recommendation = "문자열 코드를 실행하지 마세요."
    db_session.commit()
    analysis = _analysis(db_session)
    (tmp_path / "sample.js").write_text("function run(input) {\n  eval(input);\n}\n")
    absolute_result = _result(
        rule_id="secscan.javascript.eval",
        path=str(tmp_path / "sample.js"),
        severity="ERROR",
    )

    persist_normalized_findings(
        db_session,
        analysis.id,
        tmp_path,
        parse_semgrep_results([absolute_result], tmp_path),
    )
    db_session.commit()

    finding = db_session.query(Finding).one()
    assert finding.kisa_code == "KISA-002"
    assert finding.rule_name == "코드 삽입"
    assert finding.severity == "HIGH"
    assert finding.confidence == "UNKNOWN"
    assert finding.recommendation == "문자열 코드를 실행하지 마세요."
    assert finding.raw_result["path"] == "sample.js"


def test_malformed_result_rejects_entire_batch(tmp_path):
    (tmp_path / "sample.py").write_text("pass\n")
    bad = _result()
    bad["end"] = {"line": 2}
    bad["start"] = {"line": 3}
    with pytest.raises(SemgrepOutputInvalid):
        parse_semgrep_results([_result(), bad], tmp_path)


def test_catalog_schemas_do_not_expose_legacy_semgrep_rule_id():
    for schema in (CatalogItemCreate, CatalogItemUpdate, CatalogItemOut):
        assert "semgrep_rule_id" not in schema.model_fields
    with pytest.raises(ValidationError):
        CatalogItemCreate.model_validate(
            {
                "kisa_code": "TEST-001",
                "name": "테스트",
                "category": "테스트",
                "default_severity": "LOW",
                "semgrep_rule_id": "legacy.rule",
            }
        )


@pytest.mark.parametrize(
    ("fixture_name", "rule_id", "kisa_code"),
    [
        ("CommandInjection.java", "secscan.java.runtime-exec", "KISA-005"),
        ("eval_injection.js", "secscan.javascript.eval", "KISA-002"),
        ("pickle_injection.py", "secscan.python.pickle-loads", "KISA-043"),
        ("JdbcStatementSql.java", "secscan.java.jdbc-statement-sql", "KISA-001"),
        ("JdbcStatementUpdateSql.java", "secscan.java.jdbc-statement-sql", "KISA-001"),
        ("dom_innerhtml.js", "secscan.javascript.dom-innerhtml", "KISA-004"),
        ("dom_innerhtml_arrow.js", "secscan.javascript.dom-innerhtml", "KISA-004"),
        (
            "dom_innerhtml_function_expression.js",
            "secscan.javascript.dom-innerhtml",
            "KISA-004",
        ),
        ("dom_innerhtml_async_function.js", "secscan.javascript.dom-innerhtml", "KISA-004"),
        ("dom_innerhtml_async_arrow.js", "secscan.javascript.dom-innerhtml", "KISA-004"),
        ("dom_innerhtml_class_method.js", "secscan.javascript.dom-innerhtml", "KISA-004"),
        ("dom_innerhtml_object_method.js", "secscan.javascript.dom-innerhtml", "KISA-004"),
        (
            "dom_innerhtml_function_expression_multi.js",
            "secscan.javascript.dom-innerhtml",
            "KISA-004",
        ),
        ("dom_innerhtml_arrow_multi.js", "secscan.javascript.dom-innerhtml", "KISA-004"),
        (
            "dom_innerhtml_arrow_unparenthesized.js",
            "secscan.javascript.dom-innerhtml",
            "KISA-004",
        ),
        (
            "dom_innerhtml_async_function_expression.js",
            "secscan.javascript.dom-innerhtml",
            "KISA-004",
        ),
        (
            "dom_innerhtml_arrow_expression.js",
            "secscan.javascript.dom-innerhtml",
            "KISA-004",
        ),
        (
            "dom_innerhtml_async_arrow_expression.js",
            "secscan.javascript.dom-innerhtml",
            "KISA-004",
        ),
        (
            "dom_innerhtml_async_class_method.js",
            "secscan.javascript.dom-innerhtml",
            "KISA-004",
        ),
        ("open_user_path.py", "secscan.python.open-user-path", "KISA-003"),
        ("os_system_injection.py", "secscan.python.os-system", "KISA-005"),
        ("eval_injection.py", "secscan.python.eval", "KISA-002"),
        ("exec_injection.py", "secscan.python.exec", "KISA-002"),
        ("pickle_load_direct.py", "secscan.python.pickle-load", "KISA-043"),
        ("pickle_load_bytesio.py", "secscan.python.pickle-load", "KISA-043"),
        ("path_open.py", "secscan.python.path-open", "KISA-003"),
        ("function_constructor.js", "secscan.javascript.function-constructor", "KISA-002"),
        ("function_constructor_new.js", "secscan.javascript.function-constructor", "KISA-002"),
        ("dom_insert_adjacent_html.js", "secscan.javascript.dom-insert-adjacent-html", "KISA-004"),
        (
            "dom_insert_adjacent_html_template.js",
            "secscan.javascript.dom-insert-adjacent-html",
            "KISA-004",
        ),
        ("ProcessBuilderInjection.java", "secscan.java.process-builder", "KISA-005"),
        ("subprocess_run_shell.py", "secscan.python.subprocess-run-shell", "KISA-005"),
        ("subprocess_run_shell_alias.py", "secscan.python.subprocess-run-shell", "KISA-005"),
        (
            "subprocess_run_shell_from_import.py",
            "secscan.python.subprocess-run-shell",
            "KISA-005",
        ),
        ("subprocess_run_shell_const.py", "secscan.python.subprocess-run-shell", "KISA-005"),
        ("dom_innerhtml_compound_assign.js", "secscan.javascript.dom-innerhtml", "KISA-004"),
        ("dom_outerhtml.js", "secscan.javascript.dom-outerhtml", "KISA-004"),
        (
            "dom_outerhtml_compound_assign.js",
            "secscan.javascript.dom-outerhtml",
            "KISA-004",
        ),
        ("document_write.js", "secscan.javascript.document-write", "KISA-004"),
        ("document_writeln.js", "secscan.javascript.document-write", "KISA-004"),
        (
            "pickle_unpickler_load.py",
            "secscan.python.pickle-unpickler-load",
            "KISA-043",
        ),
        (
            "subprocess_popen_shell.py",
            "secscan.python.subprocess-popen-shell",
            "KISA-005",
        ),
        (
            "subprocess_call_shell.py",
            "secscan.python.subprocess-call-shell",
            "KISA-005",
        ),
        (
            "subprocess_check_call_shell.py",
            "secscan.python.subprocess-check-call-shell",
            "KISA-005",
        ),
        (
            "subprocess_check_output_shell.py",
            "secscan.python.subprocess-check-output-shell",
            "KISA-005",
        ),
        ("os_popen.py", "secscan.python.os-popen", "KISA-005"),
        (
            "subprocess_getoutput.py",
            "secscan.python.subprocess-output-shell",
            "KISA-005",
        ),
        (
            "subprocess_getstatusoutput.py",
            "secscan.python.subprocess-output-shell",
            "KISA-005",
        ),
        (
            "function_constructor_multi_arg.js",
            "secscan.javascript.function-constructor",
            "KISA-002",
        ),
        (
            "function_constructor_call_multi_arg.js",
            "secscan.javascript.function-constructor",
            "KISA-002",
        ),
        ("JdbcExecuteLargeUpdate.java", "secscan.java.jdbc-statement-sql", "KISA-001"),
        ("path_open_qualified.py", "secscan.python.path-open", "KISA-003"),
        ("path_open_import_alias.py", "secscan.python.path-open", "KISA-003"),
        ("path_open_multi_arg.py", "secscan.python.path-open", "KISA-003"),
        ("path_open_joinpath.py", "secscan.python.path-open", "KISA-003"),
        ("path_open_resolve.py", "secscan.python.path-open", "KISA-003"),
        ("path_open_variable_separated.py", "secscan.python.path-open", "KISA-003"),
        ("ProcessBuilderSeparated.java", "secscan.java.process-builder", "KISA-005"),
    ],
)
def test_real_semgrep_vulnerable_fixtures_normalize_to_mapped_findings(
    db_session,
    tmp_path,
    fixture_name,
    rule_id,
    kisa_code,
):
    seed_kisa_catalog(db_session)
    seed_kisa_rule_mappings(db_session)
    shutil.copy(FIXTURE_ROOT / "vulnerable" / fixture_name, tmp_path / fixture_name)
    analysis = _analysis(db_session)

    result = SemgrepRunner(timeout_seconds=30).run(tmp_path)
    assert [item["check_id"] for item in result.results] == [rule_id]
    persist_normalized_findings(
        db_session,
        analysis.id,
        tmp_path,
        parse_semgrep_results(result.results, tmp_path),
    )
    db_session.commit()

    findings = db_session.query(Finding).filter_by(analysis_id=analysis.id).all()
    assert len(findings) == 1
    finding = findings[0]
    assert finding.engine_rule_id == rule_id
    assert finding.kisa_code == kisa_code
    assert finding.severity == "HIGH"
    assert finding.confidence == "UNKNOWN"


@pytest.mark.parametrize(
    ("fixture_name", "rule_id"),
    [
        ("SafeCommand.java", "secscan.java.runtime-exec"),
        ("safe_eval.js", "secscan.javascript.eval"),
        ("safe_pickle.py", "secscan.python.pickle-loads"),
        ("SafeJdbcStatementSql.java", "secscan.java.jdbc-statement-sql"),
        ("safe_dom_innerhtml.js", "secscan.javascript.dom-innerhtml"),
        ("safe_open_user_path.py", "secscan.python.open-user-path"),
        ("safe_os_system.py", "secscan.python.os-system"),
        ("safe_eval.py", "secscan.python.eval"),
        ("safe_exec.py", "secscan.python.exec"),
        ("safe_module_reassigned_os_system.py", "secscan.python.os-system"),
        ("safe_local_reassigned_os_system.py", "secscan.python.os-system"),
        ("safe_imported_os_module.py", "secscan.python.os-system"),
        ("safe_pickle_load.py", "secscan.python.pickle-load"),
        ("safe_path_open.py", "secscan.python.path-open"),
        ("safe_path_open_variable_separated.py", "secscan.python.path-open"),
        ("safe_path_open_qualified.py", "secscan.python.path-open"),
        ("safe_function_constructor.js", "secscan.javascript.function-constructor"),
        ("safe_function_constructor_multi_arg.js", "secscan.javascript.function-constructor"),
        ("safe_dom_insert_adjacent_html.js", "secscan.javascript.dom-insert-adjacent-html"),
        ("SafeProcessBuilder.java", "secscan.java.process-builder"),
        ("SafeProcessBuilderMultiArg.java", "secscan.java.process-builder"),
        ("SafeProcessBuilderSeparated.java", "secscan.java.process-builder"),
        ("safe_subprocess_run_shell.py", "secscan.python.subprocess-run-shell"),
        ("safe_subprocess_run_popen.py", "secscan.python.subprocess-run-shell"),
        ("safe_dom_innerhtml_compound_assign.js", "secscan.javascript.dom-innerhtml"),
        ("safe_dom_outerhtml.js", "secscan.javascript.dom-outerhtml"),
        ("safe_dom_outerhtml_compound_assign.js", "secscan.javascript.dom-outerhtml"),
        ("safe_document_write.js", "secscan.javascript.document-write"),
        ("safe_document_writeln.js", "secscan.javascript.document-write"),
        ("safe_pickle_unpickler_load.py", "secscan.python.pickle-unpickler-load"),
        ("safe_subprocess_popen_shell.py", "secscan.python.subprocess-popen-shell"),
        (
            "safe_subprocess_popen_shell_dynamic.py",
            "secscan.python.subprocess-popen-shell",
        ),
        ("safe_subprocess_call_shell.py", "secscan.python.subprocess-call-shell"),
        (
            "safe_subprocess_call_shell_dynamic.py",
            "secscan.python.subprocess-call-shell",
        ),
        (
            "safe_subprocess_check_call_shell.py",
            "secscan.python.subprocess-check-call-shell",
        ),
        (
            "safe_subprocess_check_call_shell_dynamic.py",
            "secscan.python.subprocess-check-call-shell",
        ),
        (
            "safe_subprocess_check_output_shell.py",
            "secscan.python.subprocess-check-output-shell",
        ),
        (
            "safe_subprocess_check_output_shell_dynamic.py",
            "secscan.python.subprocess-check-output-shell",
        ),
        ("safe_os_popen.py", "secscan.python.os-popen"),
        ("safe_subprocess_getoutput.py", "secscan.python.subprocess-output-shell"),
        (
            "safe_subprocess_getstatusoutput.py",
            "secscan.python.subprocess-output-shell",
        ),
        ("SafeJdbcStatementExecute.java", "secscan.java.jdbc-statement-sql"),
        ("SafeJdbcStatementAddBatch.java", "secscan.java.jdbc-statement-sql"),
        ("safe_path_open_unrelated_receiver.py", "secscan.python.path-open"),
        ("safe_path_open_shadowed_candidate.py", "secscan.python.path-open"),
        (
            "SafeProcessBuilderUnrelatedReceiver.java",
            "secscan.java.process-builder",
        ),
        (
            "SafeProcessBuilderShadowedCandidate.java",
            "secscan.java.process-builder",
        ),
        ("SafeRuntimeExecSeparated.java", "secscan.java.runtime-exec"),
    ],
)
def test_real_semgrep_safe_fixtures_do_not_trigger_the_tested_rule(tmp_path, fixture_name, rule_id):
    shutil.copy(FIXTURE_ROOT / "safe" / fixture_name, tmp_path / fixture_name)

    result = SemgrepRunner(timeout_seconds=30).run(tmp_path)

    assert rule_id not in {result["check_id"] for result in result.results}


def test_pickle_load_open_propagation_produces_two_distinct_findings(db_session, tmp_path):
    seed_kisa_catalog(db_session)
    seed_kisa_rule_mappings(db_session)
    shutil.copy(
        FIXTURE_ROOT / "vulnerable" / "pickle_load_open_propagation.py",
        tmp_path / "pickle_load_open_propagation.py",
    )
    analysis = _analysis(db_session)

    result = SemgrepRunner(timeout_seconds=30).run(tmp_path)
    check_ids = {item["check_id"] for item in result.results}
    assert "secscan.python.open-user-path" in check_ids
    assert "secscan.python.pickle-load" in check_ids

    persist_normalized_findings(
        db_session,
        analysis.id,
        tmp_path,
        parse_semgrep_results(result.results, tmp_path),
    )
    db_session.commit()

    findings = db_session.query(Finding).filter_by(analysis_id=analysis.id).all()
    assert len(findings) == 2
    by_rule = {f.engine_rule_id: f for f in findings}
    assert by_rule["secscan.python.open-user-path"].kisa_code == "KISA-003"
    assert by_rule["secscan.python.pickle-load"].kisa_code == "KISA-043"
    assert all(f.severity == "HIGH" for f in findings)
