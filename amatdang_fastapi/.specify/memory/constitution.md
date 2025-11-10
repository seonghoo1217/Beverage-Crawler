<!--
Sync Impact Report
Version change: 0.0.0 → 1.0.0
Modified Principles:
- [PRINCIPLE_1_NAME] → Self-Describing Code (C- Floor)
- [PRINCIPLE_2_NAME] → Zero-Fault Data Pipeline
- [PRINCIPLE_3_NAME] → High-Fidelity OCR Backbone
- [PRINCIPLE_4_NAME] → Instrumented Integrity
- [PRINCIPLE_5_NAME] → Lean Dependency Discipline
Added Sections:
- Data & OCR Performance Standards
- Development Workflow & Quality Gates
Removed Sections:
- None
Templates requiring updates:
- .specify/templates/plan-template.md ✅ Constitution gates spelled out
- .specify/templates/spec-template.md ✅ Added Data Integrity & OCR Benchmarks section
- .specify/templates/tasks-template.md ✅ Embedded constitution-mandated tasks
- .specify/templates/checklist-template.md ✅ Updated categories to match principles
Follow-up TODOs:
- None
-->
# Starbucks Crawling Constitution

## Core Principles

### Self-Describing Code (C- Floor)
- Inline comments exist only for hard invariants or regulatory callouts; target ≤2% comment density by
  keeping functions short, pure, and named after their intent.
- Every merge must include a static-analysis or maintainability report that scores the touched files
  at C- or better; failing scores block release until refactored.
- Public APIs document behavior via docstrings; implementation details explain themselves through
  structure, tests, and naming rather than explanatory prose.
Rationale: Minimal commentary is viable only when the codebase is self-explanatory; enforcing a
maintainability floor prevents the pipeline from devolving into opaque scripts that jeopardize data
trust.

### Zero-Fault Data Pipeline
- Each ingestion, transform, and export stage MUST perform schema validation, duplicate detection,
  and checksum-based reconciliation before marking a batch complete.
- Pipelines run deterministically: jobs are idempotent, retries are explicit, and any warning is
  treated as a failure until investigated.
- Golden-path integration tests replicate real crawls/OCR runs and must pass in CI before new data
  connectors or transformations reach production.
Rationale: The crawler exists to deliver clean data; tolerating even a single silent failure negates
the project’s value.

### High-Fidelity OCR Backbone
- OCR components target ≥98% character accuracy or ≥95% word accuracy on the curated Starbucks data
  corpus; deviations >0.5% trigger automatic rollback.
- Maintain a labeled benchmark dataset, update it when source layouts shift, and record every test
  run to prove historical accuracy trends.
- Libraries that materially improve OCR quality are allowed, but only after benchmarking proves the
  uplift relative to the current stack.
Rationale: Data integrity hinges on OCR precision; without a measurable floor and regression history,
downstream analytics cannot be trusted.

### Instrumented Integrity
- All pipeline stages emit structured logs, metrics, and alerts that tie each record back to its OCR
  snapshot and transformation path.
- Reproducible dry runs (with seeded input) are required before production deployments; artifacts and
  run IDs are archived for audits.
- Alert thresholds map directly to escalation steps (pause crawl, roll back OCR model, reprocess
  data) and must be documented in runbooks.
Rationale: Observability is the only way to guarantee “no issues” in the data pipeline and to diagnose
any drift before users do.

### Lean Dependency Discipline
- Introduce a new library only when it demonstrably improves OCR accuracy or pipeline stability; the
  justification and evaluation notes live alongside the dependency declaration.
- Every dependency has an exit plan (version pinning, replacement, or removal) reviewed at least once
  per quarter.
- Favor standard library + existing stack first; experimental packages run in isolated spikes before
  touching production code.
Rationale: Unnecessary libraries bloat attack surface, slow audits, and obscure the performance gains
we need for OCR.

## Data & OCR Performance Standards
- Maintain up-to-date documentation of the entire data flow (crawl → OCR → normalization → export),
  including schema contracts, invariants, and validation scripts per stage.
- Benchmark OCR weekly (or after each model/config change) against the golden dataset; store reports,
  confusion matrices, and false-positive/negative samples for traceability.
- Define acceptable latency and throughput for pipeline stages so performance optimizations do not
  compromise accuracy; publish these targets with every feature plan.
- Treat reconciliation reports and anomaly dashboards as release artifacts—no deployment is complete
  without attaching them to the change log.

## Development Workflow & Quality Gates
- Design docs (specs, plans, tasks) must explicitly record how each principle is satisfied; work
  cannot start while a gate is ambiguous.
- CI runs readability checks, schema/duplication tests, OCR benchmarks, and dependency audits on
  every PR; failures block merges without exception.
- Code reviews certify that added dependencies were justified, that metrics/logging coverage grew
  with new functionality, and that recoverability steps are documented.
- Releases include a dry-run report, OCR accuracy summary, and dependency delta; operations receives
  these artifacts before deployment approval.

## Governance
- This constitution supersedes conflicting guidance; exceptions require a written RFC describing the
  risk, mitigation, and rollback plan approved by the project maintainer.
- Amendments follow Semantic Versioning: MAJOR for removing/replacing principles, MINOR for adding
  principles/sections or materially expanding requirements, PATCH for clarifications and typo fixes.
- Ratification history is immutable; new amendments append to the change log with supporting evidence
  (benchmarks, audits) stored in the repo.
- Compliance is reviewed every iteration: specs/plans are checked up front, CI enforces gates during
  development, and quarterly audits verify dependency hygiene + OCR accuracy trends.

**Version**: 1.0.0 | **Ratified**: 2025-11-10 | **Last Amended**: 2025-11-10
