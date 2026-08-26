# SecScan Agent Instructions

## Project source of truth

- The primary requirements source is `docs/원본_요구사항목록.docx`.
- Derived documents may interpret the source, but must not override it.
- If the source is ambiguous, mark the item as unresolved and ask the user before making a material decision.
- Do not reintroduce an unconfirmed limit on the number of implemented KISA detection rules.

## Shared project rules

- Read `docs/development-workflow.md` before making repository-level changes.
- Read `DESIGN.md` before making frontend or UI decisions.
- Follow `CONTRIBUTING.md` for implementation, testing, commit, PR, and troubleshooting rules.
- Do not commit secrets, real credentials, uploaded source code, generated artifacts, or local agent state.
- Every material bug or environment problem must be recorded with `docs/templates/troubleshooting.md`.

## Codex role

Codex is the primary implementation and verification agent.

- Inspect the repository and trace behavior across backend, frontend, database, and documentation.
- Implement approved changes in the appropriate feature branch.
- Add or update tests with the implementation.
- Run proportionate validation and report exact evidence.
- Update requirements matrices and troubleshooting records when the work changes them.
- Do not silently change product scope or unresolved requirements.

## Claude role

Claude is the design and review partner.

- Review product and UI decisions against `DESIGN.md` and the original requirements.
- Review code changes for correctness, security, regression risk, and missing tests.
- Check requirement coverage and challenge unsupported assumptions.
- Review troubleshooting records for reproducibility and completeness.
- Suggest changes through PR comments or review notes; implementation remains with the active coding agent unless explicitly requested.

## Review handoff

For a meaningful change, use this sequence:

```text
Codex: inspect and implement
→ Codex: run tests and collect evidence
→ Claude: review diff, requirements, security, and tests
→ Codex: address accepted findings
→ Codex: rerun validation
→ human: approve and merge
```

## Stop conditions

- Stop and ask the user when a requirement interpretation changes scope, security policy, data model, or deployment behavior.
- Stop before destructive operations or external repository changes that require credentials.
- If a test or deployment issue is not fully resolved, document it with the troubleshooting template instead of hiding it.
