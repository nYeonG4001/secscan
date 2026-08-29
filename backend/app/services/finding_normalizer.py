"""E5 Finding 정규화, KISA 스냅샷 및 제한된 코드 조각 추출."""

from __future__ import annotations

import hashlib
from pathlib import Path

from sqlalchemy.orm import Session

from app.models.finding import Finding
from app.models.kisa_catalog import KisaCatalog
from app.models.kisa_rule_mapping import KisaRuleMapping
from app.services.semgrep_parser import NormalizedFinding


def persist_normalized_findings(
    db: Session, analysis_id: int, snapshot_root: Path, findings: list[NormalizedFinding]
) -> int:
    mappings = {
        mapping.engine_rule_id: mapping.kisa_code
        for mapping in db.query(KisaRuleMapping).filter(KisaRuleMapping.engine == "semgrep")
    }
    catalogs = {
        item.kisa_code: item
        for item in db.query(KisaCatalog).filter(
            KisaCatalog.kisa_code.in_(mappings.values())
        )
    }
    seen: set[str] = set()
    for normalized in findings:
        fingerprint = finding_fingerprint(normalized)
        if fingerprint in seen:
            continue
        seen.add(fingerprint)
        kisa_code = mappings.get(normalized.engine_rule_id)
        catalog = catalogs.get(kisa_code) if kisa_code else None
        if kisa_code and catalog is None:
            raise ValueError("mapping target is missing from catalog")
        db.add(
            Finding(
                analysis_id=analysis_id,
                kisa_code=kisa_code,
                criterion_id=catalog.criterion_id if catalog else None,
                engine_rule_id=normalized.engine_rule_id,
                rule_name=catalog.name if catalog else normalized.rule_name,
                severity=(
                    catalog.default_severity
                    if catalog
                    else normalize_severity(normalized.severity)
                ),
                confidence=normalized.confidence,
                language=normalized.language,
                file_path=normalized.file_path,
                line=normalized.line,
                end_line=normalized.end_line,
                message=normalized.message,
                evidence=normalized.evidence,
                recommendation=catalog.recommendation if catalog else None,
                raw_result=normalized.raw_result,
                code_snippet=extract_code_snippet(
                    snapshot_root,
                    normalized.file_path,
                    normalized.line,
                    normalized.end_line,
                ),
                finding_fingerprint=fingerprint,
            )
        )
    db.flush()
    return len(seen)


def finding_fingerprint(finding: NormalizedFinding) -> str:
    end = (
        finding.end_line
        if finding.end_line is not None
        else finding.line if finding.line is not None else "NO_LINE"
    )
    payload = "\x00".join(
        (finding.engine_rule_id, finding.file_path, str(finding.line), str(end))
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def normalize_severity(value: str | None) -> str:
    source = value.upper() if isinstance(value, str) else ""
    if source == "CRITICAL":
        return "CRITICAL"
    if source in {"HIGH", "ERROR"}:
        return "HIGH"
    if source in {"MEDIUM", "WARNING"}:
        return "MEDIUM"
    if source in {"LOW", "INFO"}:
        return "LOW"
    return "UNKNOWN"


def extract_code_snippet(
    snapshot_root: Path,
    file_path: str,
    line: int | None,
    end_line: int | None,
) -> str | None:
    if line is None:
        return None
    try:
        root = snapshot_root.resolve(strict=True)
        candidate = (root / file_path).resolve(strict=True)
        candidate.relative_to(root)
        lines = candidate.read_text(encoding="utf-8").splitlines()
        end = end_line or line
        start_index, end_index = max(0, line - 3), min(len(lines), end + 2)
        selected = lines[start_index:end_index]
        if len(selected) > 20:
            selected = selected[:10] + ["... [중간 생략] ..."] + selected[-10:]
        snippet = "\n".join(selected)
        return snippet.encode("utf-8")[: 8 * 1024].decode("utf-8", errors="ignore")
    except (OSError, UnicodeError, ValueError):
        return None
