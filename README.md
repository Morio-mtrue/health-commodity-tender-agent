# Health Commodity Tender Evaluation Workbench

A local evidence review workbench for a public-sector health commodity tender committee. It inventories a closed tender and synthetic bids, locks sourced criteria through human review, calculates price observations, and prepares an unsigned draft package. It never selects a winner or issues an award.

## Run on Windows

Prerequisites: [uv](https://docs.astral.sh/uv/getting-started/installation/) and [Node.js LTS](https://nodejs.org/). Tested with Python 3.12.14. Dependencies are pinned in `uv.lock` and `package-lock.json`.

```powershell
./scripts/start.ps1
```

Open **http://127.0.0.1:8000**. Choose **Load synthetic case**, compile the plan, inspect each citation, and enter your reviewer name to lock it. Then evaluate the bids, inspect the draft, and approve export. Approvals bind to the exact plan or draft digest.

The command installs project-local dependencies and starts a loopback-only server. It does not install a model runtime or download weights. The structured synthetic fixture runs without a model; an open-model workflow is a separate required submission task.

To include the portable CPU runtime and checksum-verified Qwen weights (about 1.12 GB), use `./scripts/start.ps1 -WithModel`. No system model installation is needed. Select `qwen2.5-1.5b-instruct-q4_k_m.gguf` in extraction settings. See [model setup](docs/MODEL_SETUP.md).

## Implemented

- Four real custom stdio MCP tools: `register_case`, `compile_evaluation_plan`, `evaluate_bid_pack`, and `draft_evaluation_file`.
- LangGraph with separate human plan and export interrupts.
- Official Filesystem MCP `read_text_file`, restricted to the active case directory, with audit records.
- SHA-256 inventory, native PDF/text extraction, table bounding boxes, and exact page citations.
- Synthetic sourced criteria, addendum supersession, manual plan editing, versioned artifacts, and new locks after edits.
- Evidence matrix, conservative abstention, Decimal arithmetic, pack normalization, tender-date expiry observations, and explicit FX rules.
- Citation validation before accepting findings or drafting; submitted prices preserved.
- Named local review gates, stale approval rejection, changed-source/draft detection, and prior run history.
- Approved ZIP with an escaped offline HTML report, CSV matrix, JSON evidence/prices/exceptions, originals, and complete logs.
- Hash-linked audit events with database triggers preventing routine edits or deletes.

## Verification

The core suite passed **30 tests with one observed expected failure** through the one-command check. An actual MCP integration run invoked all four custom tools and the borrowed Filesystem server, produced **18 cited evidence cells and nine price rows**, and completed in **13.52 seconds**. Automated approvals are explicitly labelled **TEST SIMULATION**; they are not a committee approval or an open-model demonstration. See [EVALS.md](EVALS.md).

```powershell
./scripts/start.ps1 -CheckOnly
uv run python -m scripts.mcp_smoke
```

Test artifacts stay in ignored `outputs/`. Restricted Windows sandboxes can block SQLite/pytest temporary folders; the core suite was verified with approved local execution.

## Public reference and model

Selected reference: [KEMSA/OIT05/2024-2026](https://kemsa.go.ke/tender/view/kemsa-oit05-2024-2026), liquid dosage forms, inhalation products, and topical formulations. The archive marks it closed and lists two addenda. The archive and extension notice disagree on the exact closing date; original/addendum retrieval encounters timeouts. [Reference notes](docs/REFERENCE_CASE.md) retain the discrepancy and known URLs. No finding is claimed against that tender.

The included tender, addendum, registrations, and bids are original synthetic fixtures, not transcriptions of the public reference. Their products are not asserted to be its actual schedule.

Local Ollama and portable llama.cpp adapters record the model/runtime identity, prompt version, and usage. They validate sourced manual criteria. The portable runtime was blocked by Windows Application Control before inference; a standard Ollama installation is being prepared. No successful open-model run or bake-off has completed. See [model setup](docs/MODEL_SETUP.md).

## Current limitations

- OCR is unconfigured. Image-only pages become `OCR_FAILED`; findings remain unresolved. A genuinely scanned fixture demonstrates this failure.
- Public PDF criteria are model-proposed manual rules. A human must verify completeness and define any deterministic mappings before locking them.
- Native/unstructured bid interpretation is manual/unresolved; deterministic extraction works on the included structured synthetic bids.
- Allowlisted public adapters retain retrieval/status metadata but do not yet parse verified PPB/debarment records or dated comparable benchmarks. Portal availability never establishes a registry match; all current reference checks remain unresolved.
- Weighted scoring is rejected. Plan edits preserve history and rerun the whole case rather than only affected checks.
- Graph checkpoints are in memory; durable case state reconstructs gates after restart. In-flight model calls are not resumed byte for byte.
- Reviewer names are local demo attestations, not enterprise authentication. Session/origin/host checks stop routine cross-origin actions; a machine administrator can modify local files/database. No production readiness is claimed.

## Data and licence

Use only closed public tenders and clearly labelled synthetic bids. Embedded URLs/instructions are never followed. Original documents stay unchanged. Advisory references cannot introduce unpublished criteria.

Original code is MIT licensed. External documents, models, packages, and registers keep their own licences. Do not redistribute data without permission. `local_data/`, `models/`, `.runtime/`, `.env`, and `outputs/` are ignored. The user authorized the public [Morio-mtrue/health-commodity-tender-agent repository](https://github.com/Morio-mtrue/health-commodity-tender-agent). No external dataset is redistributed.

## Submission status

The user explicitly waived build-start confirmation and authorized implementation. Organizer timing has not been certified.

Still required: retrieve/reconcile the public tender and every addendum; select actual schedule lines; practitioner review; local open-model workflow and five-run variation measurement; clean-machine setup check; public repository; and an unedited public video under three minutes. See [inputs](docs/INPUTS.md).
