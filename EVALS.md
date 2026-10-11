# Evaluation record

Final one-command check: **40 PASS, one strict XFAIL**, 50.48 seconds, exit code zero. Five document-scoped Qwen runs completed in 100.78–193.20 seconds, each with seven valid source spans and correct addendum precedence. Model criteria remained manual: 18 unresolved cells, zero automatic price rows, and explicitly simulated approvals. This is engineering evidence, not practitioner or committee approval.

## Observed local results

Core command: `.venv/Scripts/python.exe -m pytest -q --basetemp=outputs/test-run-002 --junitxml=outputs/test-results.xml`.

Observed: **20 PASS, one XFAIL**, 64.26 seconds. This was approved execution outside the restrictive Windows sandbox; initial sandbox attempts failed to create/open temporary directories/databases and are not counted as product test passes. The subsequent regression run passed the same 20 tests and one XFAIL in 19.21 seconds, after the validation and export-log changes.

Actual MCP command: `.venv/Scripts/python.exe -m scripts.mcp_smoke`.

Observed on 11 October 2026 at 08:19 Africa/Nairobi: all four custom tools invoked through stdio, official Filesystem `read_text_file` SUCCESS, both graph gates exercised, 18 cited evidence cells, nine price rows, an unsigned exported ZIP, and valid audit integrity. **13.52 seconds**. Approvals were labelled **TEST SIMULATION**, not performed by a human committee. Model run: **false**.

Versions: Python 3.12.14, mcp 1.30.0, LangGraph 1.2.14, Pydantic 2.14.0, pdfplumber 0.11.10, FastAPI 0.143.0; borrowed Filesystem MCP 1.0.0.

Latest full verification used the real one-command entry point `./scripts/start.ps1 -CheckOnly`: **30 PASS, one XFAIL**, 63.67 seconds. Added checks cover local-only model endpoints, credentials/context rejection, and resumable downloads with exact ranges and final checksums.

The first actual portable-model workflow attempt on 11 October 2026 failed after **12.88 seconds**, with a valid audit trail. The model never served an inference request: loading the official runtime DLL produced **WinError 4551, Application Control policy blocked this file**. Signed Ollama subsequently installed successfully and serves the verified GGUF on CPU. Windows security policy was not changed.

Fresh checkout check: public commit `88842ea` was archived into a separate directory, installed with fresh project Python/npm dependencies, and passed **30 tests, one XFAIL**, in **30.13 seconds**. Its actual MCP smoke run completed in **19.02 seconds**, invoking all four custom tools and borrowed Filesystem, producing 18 cells/nine price rows, with valid audit integrity. This verifies a fresh checkout on the same Windows installation; it is not a clean-OS test.

After local-only/cloud alias controls, source-role validation, raw proposal preservation, quotation binding, document-scoped extraction, and sourced supersession checks, the suite passed **39 tests, one XFAIL**, in **40.19 seconds**, exit code zero. The JUnit reporter emitted a Windows WMI memory diagnostic after the assertions. After adding the inactive-criterion source guard, `./scripts/start.ps1 -CheckOnly` passed **40 tests, one XFAIL**, in **50.48 seconds**, without that reporting diagnostic.

## Actual model development observations

Ollama 0.40.3 serves `tender-qwen:1.5b-q4`, imported from the publisher-checksummed Qwen GGUF. Its manifest digest is `2304751c9569070cb5bd3ef97e4f7dd5f769cee5ed635fbd6775ceb62de6b7e6`. Inputs are native-text renditions of the original synthetic tender/addendum, not prestructured criteria JSON; bids remain original structured synthetic fixtures.

- The first Ollama attempt hit the original 120-second timeout after 136.39 seconds overall. Bounded CPU extraction and transport budgets were extended.
- A completed response was rejected after 190.38 seconds because display wording paraphrased the source quote.
- A quotation-only response was rejected after 119.72 seconds because citations were put in the wrong JSON field and the addendum was omitted. Its raw proposal is preserved.
- JSON-schema-constrained prompt v2 completed in 124.16 seconds, with seven valid source spans but no supersession link. All 21 findings stayed unresolved; no price checks were invented.
- Prompt v3 invented unsupported supersession links and omitted the addendum. One simulated run completed; repeats were stopped. This exposed a missing semantic source check, which is now covered by a regression test. Such a proposal can no longer deactivate unrelated original criteria.
- Prompt v4 extracts one document per request. Original tender requests constrain supersedes to null; the plan validator requires an addendum quotation explicitly replacing the named criterion. The verified run found seven requirements, linked T01A to T01, and completed in 193.20 seconds. Every accepted quotation occurs on its source page. It emitted 18 unresolved cells and no price rows because deterministic mappings are reserved for human review.

The exact gold wording metric is distinct from source-span coverage: the model includes published IDs/headings in its quotes, so exact equality to bare gold sentences is zero even when each cited span contains its correct, independently identified requirement. Source-span matching uses criterion ID, original document ID, and the full gold requirement text; each criterion can match only its own gold requirement. Do not present source-span coverage as perfect bare-sentence extraction.

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

## Five fixed-prompt model repeats

All five complete MCP workflows used the same Qwen manifest, prompt v4 hash `8847f90a0dfb1f7bd7ed944c411ac72ffb478bcab37458c421efff0f3d74a9b0`, and base output-schema hash `b97d11f74f772252bed8b58f79049f2c0e73e860344800398cbe6ba169be39b6`. Per-document schema hashes and source hashes are retained in each run. All approvals are TEST SIMULATION.

| Run | Seconds | Gold source spans | Valid citations | Correct supersession | Outcome |
| --- | ---: | ---: | ---: | --- | --- |
| 1 | 193.20 | 7/7 | 7/7 | Yes | Exported |
| 2 | 166.64 | 7/7 | 7/7 | Yes | Exported |
| 3 | 125.77 | 7/7 | 7/7 | Yes | Exported |
| 4 | 121.53 | 7/7 | 7/7 | Yes | Exported |
| 5 | 100.78 | 7/7 | 7/7 | Yes | Exported |

Mean **141.58 seconds**, sample standard deviation **37.45 seconds**, range **100.78–193.20 seconds**. Extracted source wording was identical across all five runs, including its extra headings; strict bare-sentence equality remained zero. Every run retained correct addendum precedence, 18 manual unresolved cells, zero price rows, actual borrowed MCP success, and valid audit integrity. These five easy synthetic inputs do not establish general extraction accuracy on long public PDFs or stability for a stronger model.

Ollama `/api/ps` reported allocated runtime size **1,750,576,659 bytes** (about 1.63 GiB), **zero VRAM**, and 16,384-token context in every run. This is the runtime's allocation observation, not measured whole-machine peak RAM. Hosted inference API cost was **zero**; electricity, installation/download costs, and human time were not measured. The model used two document requests within each custom compile call.

Machine-readable measurements remain local in `outputs/model-evaluation-result.json` and `outputs/model-evaluation-summary.json`, with original case manifests, proposals, exports, and logs. Cases/weights are not redistributed in Git.

## Observed scanned-page failure

The test `test_scanned_page_ocr_known_failure` creates an image-only synthetic certificate page and expects its text. Extraction returns empty text with `OCR_FAILED`. That assertion actually failed and is declared strict XFAIL, so accidental unexpected success would fail the suite. This is not an invented failure or a repaired feature. Next: add a sandboxed PDF sanitization step, selective OCR, rotation handling, and page-level provenance, then validate on poor merged tables before claiming support.

## Other limits and remaining measurements

Native PDF extraction is tested, but mixed-page OCR is unsupported. Public KEMSA downloads timed out, including both addenda. Public PPB/debarment checks do not yet parse verified records. A successful local open-weights workflow is measured; broader evidence precision/recall, a stronger-model bake-off, practitioner corrections, actual human pause duration, a public video, and clean-OS setup remain unmeasured.

Structured-fixture MCP durations exclude model inference and real human review. Model workflow durations include inference, actual custom/borrowed transport, and simulated approvals. They do not establish the full public-tender acceptance condition with actual human review.

Machine-readable local evidence: ignored `outputs/final-check-result.json`, `outputs/test-results.xml` (earlier 39-test JUnit run), `outputs/mcp-integration-result.json`, model measurements, and corresponding case manifests/artifacts. Fixture definitions and assertions are committed in `sample_case/fixture.py` and `tests/`.
