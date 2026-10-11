# Evaluation record

## Observed local results

Core command: `.venv/Scripts/python.exe -m pytest -q --basetemp=outputs/test-run-002 --junitxml=outputs/test-results.xml`.

Observed: **20 PASS, one XFAIL**, 64.26 seconds. This was approved execution outside the restrictive Windows sandbox; initial sandbox attempts failed to create/open temporary directories/databases and are not counted as product test passes. The subsequent regression run passed the same 20 tests and one XFAIL in 19.21 seconds, after the validation and export-log changes.

Actual MCP command: `.venv/Scripts/python.exe -m scripts.mcp_smoke`.

Observed on 11 October 2026 at 08:19 Africa/Nairobi: all four custom tools invoked through stdio, official Filesystem `read_text_file` SUCCESS, both graph gates exercised, 18 cited evidence cells, nine price rows, an unsigned exported ZIP, and valid audit integrity. **13.52 seconds**. Approvals were labelled **TEST SIMULATION**, not performed by a human committee. Model run: **false**.

Versions: Python 3.12.14, mcp 1.30.0, LangGraph 1.2.14, Pydantic 2.14.0, pdfplumber 0.11.10, FastAPI 0.143.0; borrowed Filesystem MCP 1.0.0.

Latest full verification used the real one-command entry point `./scripts/start.ps1 -CheckOnly`: **30 PASS, one XFAIL**, 63.67 seconds. Added checks cover local-only model endpoints, credentials/context rejection, and resumable downloads with exact ranges and final checksums.

The first actual portable-model workflow attempt on 11 October 2026 failed after **12.88 seconds**, with a valid audit trail. The model never served an inference request: loading the official runtime DLL produced **WinError 4551, Application Control policy blocked this file**. This is a runtime failure, not a measurement of model quality. A standard official Ollama installation is being prepared; no successful model workflow is claimed yet.

| Task | Result | Evidence |
| --- | --- | --- |
| Clean native-text PDF | PASS | Two generated source pages retain native text and page numbers |
| Addendum precedence | PASS | T01 deactivated; T01A with 18-month minimum affects checks |
| Mandatory certificate absent | PASS | Cited requirement plus parsed inventory; no invented certificate |
| Ambiguous equivalent strength | PASS | UNRESOLVED with submitted and tender citations |
| Pack normalization and extended discrepancy | PASS | Submitted 59,000 preserved; calculated 60,000; 1.2 KES/mL |
| Currency conversion | PASS | Explicit dated/source/method rule computes exact result; missing rule abstains |
| Similar debarred name/different identifier | PASS | No fuzzy adverse flag; exact match sent for review |
| Submitted expired registration | PASS | Tender-date observation cited; portal verification still unresolved |
| Embedded prompt injection | PASS | Cannot introduce criteria, unlock plan, or authorize export |
| Corrupt bid attachment | PASS | Parser failure causes UNRESOLVED, not a missing-certificate accusation |
| Five deterministic repeats | PASS | Evidence/calculation agreement; history retained; not model stability |
| Unsourced finding | PASS | Schema rejects finding with empty citations |
| Invented quotation / bid-proposed rule | PASS | Source validation rejects both |
| Changed original file | PASS | Hash mismatch blocks evaluation |
| Plan revision | PASS | New human lock required; current run cleared, prior run retained |
| Stale export approval | PASS | Wrong digest rejected; valid simulated approval yields unsigned package and complete logs |
| Draft changed after review | PASS | Export rejected |
| Path traversal / audit edits | PASS | Escape rejected and normal audit deletion blocked |
| UI session/origin gate | PASS | Missing token and cross-origin approvals rejected |
| Unapproved download / foreign host | PASS | Download blocked and unexpected host rejected |
| Image-only scanned-page OCR | **XFAIL (observed unresolved failure)** | Real image-only fixture yields no native text; OCR is unconfigured |

## Known failure

The test `test_scanned_page_ocr_known_failure` creates an image-only synthetic certificate page and expects its text. Extraction returns empty text with `OCR_FAILED`. That assertion actually failed and is declared strict XFAIL, so accidental unexpected success would fail the suite. This is not an invented failure or a repaired feature. Next: add a sandboxed PDF sanitization step, selective OCR, rotation handling, and page-level provenance, then validate on poor merged tables before claiming support.

## Other limits and remaining measurements

Native PDF extraction is tested, but native/scanned mixed-page OCR is not supported. Public KEMSA downloads timed out. Public PPB/debarment checks do not yet parse verified records. No open-weights workflow, model extraction recall, evidence precision/recall, five-model-run agreement, memory/cost measurement, practitioner correction count, public video, or clean-machine setup is claimed.

The recorded MCP duration is an automated synthetic integration duration, excluding real human review and model inference. It does not establish the complete open-model under-20-minute acceptance condition.

Machine-readable local evidence: ignored `outputs/test-results.xml`, `outputs/mcp-integration-result.json`, and the corresponding case manifests/artifacts. Fixture definitions and assertions are committed in `sample_case/fixture.py` and `tests/`.
