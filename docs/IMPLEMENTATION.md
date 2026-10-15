# Implementation backlog

**Current phase (15 October 2026): synthetic bid evaluation plus real Kenya OCDS award history, an agent planner with bounded retry, real MCP transport, and measured local open-model runs.** This was the original build backlog; the public MIT repository is created. This backlog preserves the intended sequence; README.md and EVALS.md distinguish observed behavior from unfinished scope. Public corpus retrieval, practitioner and human review, OCR, verified external records, a stronger-model comparison, and the public video remain outstanding.

## 1. Corpus and environment

- Select a demonstrably closed tender and addenda; record provenance and redistribution restrictions.
- Freeze three to five product lines, synthetic bidder scenarios, and gold criteria.
- Review the labels with a practitioner.
- Lock tested Python, MCP, orchestration, parser, and frontend dependencies.
- Provide and verify a one-command Windows setup in a fresh project environment.

Exit: reproducible environment and frozen demo corpus.

## 2. Case store and plan compiler

- Define strict citation, criterion, evidence, product, finding, approval, and run schemas.
- Register a case with size/type/page limits, original hashes, addendum links, and trusted inventory.
- Extract native PDF text; support explicit selective OCR failure.
- Produce a draft plan with exact quotations and source hashes/pages/sections.
- Add review/edit/lock UI with a named approval bound to the plan hash.
- Log each tool call including inputs, outputs, timestamp, duration, status, and errors.

Exit: one sourced plan can be inspected and locked by a human.

## 3. Evidence and calculations

- Evaluate only against the locked plan and verified document manifest.
- Trace evidence to source pages and table coordinates where available.
- Implement Decimal arithmetic, pack/base-unit normalization, quantities, dates, and explicit currency conversion.
- Preserve submitted prices and flag discrepancies without changing the bid.
- Distinguish absent evidence, contradictory evidence, ambiguity, and inaccessible sources.
- Validate citations before accepting a finding.

Exit: one synthetic bid evaluates end to end with reproducible calculations.

## 4. Orchestration and official sources

- Implement the explicit LangGraph states and approval interrupts with bounded retry policies.
- Connect official Filesystem MCP under a case-scoped root and audit real invocations.
- Add PPB and PPRA adapters with official-domain allowlists, retrieval/as-of metadata, and timeout recovery.
- Require exact identity evidence for debarment observations; no fuzzy adverse matching.
- Keep KEML/KEMSL and comparable price benchmarks advisory unless authorized by the tender.
- Verify Windows traversal and symlink boundaries.

Exit: source failures remain visible and unresolved; borrowed MCP actually runs.

## 5. Reports and local model

- Generate a compliance matrix, evidence ledger, calculated price table, unresolved queue, and unsigned report.
- Bind export approval to the precise draft digest; leave committee recommendation/signature/award fields blank.
- Test candidate local open-weights models against actual fixtures and machine resources.
- Pin the chosen model and prompt; complete and measure an actual full model workflow.
- Support plan revisions, new human locks, dependency invalidation, and preserved prior runs.

Exit: full reviewable package and a measured open-model run.

## 6. Verification and submission

- Run at least eight planned tasks; target all tasks in EVALS.md.
- Repeat the main case five times and report variation honestly.
- Record one actually observed unresolved failure.
- Verify clean setup and under-20-minute runtime.
- Update README/architecture/results to match observed behavior.
- Prepare the public repository, 300-word description, and unedited under-three-minute demo.

Exit: actual acceptance evidence and reviewable submission artifacts. Publication and submission status must remain explicit.
