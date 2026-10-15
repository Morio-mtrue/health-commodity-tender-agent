# Evaluation record

Everything below was observed on one Windows 11 laptop (about 15.7 GiB RAM, CPU only). Automated approvals are labelled **TEST SIMULATION**; none is a committee decision.

## Summary (15 October 2026)

| Check | Result |
| --- | --- |
| Test suite (`./scripts/start.ps1 -CheckOnly` or `pytest -q`) | **49 passed, 1 strict expected failure**, 11.92 s on the final run (90.40 s earlier under load) |
| Full agent run over real MCP stdio with real OCDS data (`scripts.mcp_smoke`) | PASS in 4 of 4 runs, 29.89 s to 56.27 s, identical results |
| Qwen2.5-1.5B workflows through the new graph (`scripts.model_eval --native-text --repeats 3`) | **3 of 3 exported**, 7/7 gold source spans each, correct addendum precedence, first-attempt success, 193.06 s to 225.00 s per full workflow |
| Unfixed failure | Image-only scanned page: no OCR (strict XFAIL) |
| Untested by a real model | The retry-with-feedback loop (Qwen never failed validation in these runs) |

## Test tasks

Each row is an automated test in `tests/`. PASS means the assertion held in the 15 October run.

| # | Task | Result | Evidence |
| --- | --- | --- | --- |
| 1 | Clean native-text PDF keeps page numbers | PASS | Two generated pages, text and page numbers retained |
| 2 | Addendum supersedes original criterion | PASS | T01 inactive; T01A (18 months) used |
| 3 | Unsourced supersession cannot hide a criterion | PASS | Rejected unless the addendum quote names it |
| 4 | Inactive flag cannot hide an unsuperseded rule | PASS | Revision rejected |
| 5 | Model quotation bound to its registered source | PASS | Invented quote rejected; hash from manifest |
| 6 | Mandatory certificate absent | PASS | BID_B P02 cites the requirement and every bid page that was searched (document hash and page); nothing invented |
| 7 | Ambiguous equivalent strength | PASS | UNRESOLVED with tender and bid citations |
| 8 | Pack normalization and price discrepancy | PASS | Submitted 59,000 preserved; calculated 60,000; 1.2 KES/mL |
| 9 | Currency conversion needs a published rule | PASS | Missing rule abstains; explicit rule computes |
| 10 | Similar debarred name, different identifier | PASS | No fuzzy adverse flag |
| 11 | Submitted registration expired before closing | PASS | Cited date observation; registry still unresolved |
| 12 | Prompt injection in a bid | PASS | Cannot add criteria, unlock, or approve |
| 13 | Corrupt bid attachment | PASS | UNRESOLVED, not a missing-document accusation |
| 14 | Five deterministic repeats agree | PASS | Same statuses and calculations; history kept |
| 15 | Finding without citation | PASS | Schema rejects it |
| 16 | Tender posing as bid evidence | PASS | Rejected at registration |
| 17 | Bad citation or bid-introduced rule | PASS | Both rejected |
| 18 | Changed original file | PASS | Hash mismatch stops evaluation |
| 19 | Plan revision | PASS | New lock required; prior run kept |
| 20 | Stale or wrong export approval | PASS | Wrong digest rejected; valid one exports unsigned package with full log |
| 21 | Draft changed after review | PASS | Export rejected |
| 22 | Path traversal and audit deletion | PASS | Both blocked |
| 23 | UI session and origin gate | PASS | Missing token and cross-origin approvals rejected |
| 24 | Unapproved download and foreign host | PASS | Both blocked |
| 25 | Local model safety (12 tests) | PASS | Remote or credentialed endpoints, unknown backend, cloud tags and remote aliases rejected before any prompt is sent; context limit; bids excluded from extraction; truncated output rejected |
| 26 | Resumable model download (2 tests) | PASS | Exact ranges and final checksum |
| 27 | **OCDS messy records** | PASS | Numbered supplier names normalized and flagged; zero and top-1% values excluded from statistics; inverted tender period flagged; every value cites file hash, line and pointer |
| 28 | **OCDS contact details never stored** | PASS | Test email and phone absent from the whole index dump |
| 29 | **Closing date reconciled against OCDS** | PASS | Declared 2024-11-12 versus published 2024-11-13 recorded as cited UNRESOLVED; carried into the draft queue |
| 30 | **OCDS index missing** | PASS | SOURCE_UNAVAILABLE observation, no crash |
| 31 | **Agent plans from the borrowed manifest** | PASS | Work plan lists award history; pauses at the plan gate |
| 32 | **Borrowed MCP down** | PASS | Plans from local store, records UNRESOLVED, continues |
| 33 | **Compile retry with validator feedback** | PASS | Bad quote rejected; second attempt receives the error and succeeds; one RETRY event logged |
| 34 | **Retry limit reached** | PASS | Three attempts, then HUMAN_RECOVERY_REQUIRED; no plan invented |
| 35 | **Native tender with no model** | PASS | One attempt, then stops with the reason |
| 36 | **Every tool call logged against its case** | PASS | A positional case ID still files the event under the case, so the exported log includes `search_award_history` |
| 37 | Image-only scanned certificate | **XFAIL** | No native text; OCR not configured |

Rows 33 and 34 use a simulated model that returns a wrong quotation on purpose. That is the only way to force the failure deterministically, and it means the retry loop is tested, not observed with Qwen.

## Defects found in the final review (15 October 2026, 22:30 EAT)

A manual walk-through of the exported package found two defects, both fixed with regression tests (rows 6 and 36) that fail on the earlier code:

- The MCP server passed `case_id` positionally to `search_award_history`, so its audit event was filed under the annex ID and left out of the case's exported log. The decorator now finds the case ID in any position, and the server passes keywords.
- An absence finding against a bidder cited only the tender requirement. It now also cites each searched bid page, so the adverse observation names its source.

A real MCP run after the fix (26.55 s) shows `search_award_history` STARTED and SUCCESS in the case log and BID_B P02 citing `doc_001` and `doc_004`.

## Full agent run over real MCP transport

`uv run python -m scripts.mcp_smoke` starts the real procurement MCP server and the borrowed Filesystem server as stdio subprocesses and runs the whole graph with TEST SIMULATION approvals.

| Run | Seconds | Custom MCP calls | Borrowed read | Evidence cells | Price rows | Award history | Audit chain |
| --- | ---: | --- | --- | ---: | ---: | --- | --- |
| 1 (cold) | 56.27 | register, compile, search_award_history, evaluate, draft | SUCCESS | 18 | 9 | FOUND, 1 closing-date observation | valid |
| 2 | 41.98 | same | SUCCESS | 18 | 9 | same | valid |
| 3 | 34.31 | same | SUCCESS | 18 | 9 | same | valid |
| 4 | 29.89 | same | SUCCESS | 18 | 9 | same | valid |

The result is identical in every run; only time varies. Each MCP call starts a fresh server subprocess, and the integration audit database grows with every run, which accounts for most of the time. The 11 October version of this run (four tools, no award history) took 13.52 s. No model is used here.

## Open-weights model runs (15 October 2026)

Qwen2.5-1.5B-Instruct Q4_K_M, Ollama 0.40.3 on CPU, manifest digest `2304751c...b7e6`, prompt `criteria-v4`, temperature 0, document-scoped extraction. Inputs are native-text versions of the synthetic tender and addendum; bids are structured synthetic files. Each run is a full graph: inspect, compile with the model, award history, simulated plan lock, evaluate, draft, simulated export.

| Run | Full workflow (s) | Model inference (s) | Output tokens | Compile attempts | Gold source spans | Supersession | Evidence cells | Outcome |
| --- | ---: | ---: | ---: | ---: | ---: | --- | --- | --- |
| 1 | 197.97 | 156.0 | 898 | 1 | 7/7 | correct | 18 UNRESOLVED | exported |
| 2 | 225.00 | 134.6 | 898 | 1 | 7/7 | correct | 18 UNRESOLVED | exported |
| 3 | 193.06 | 119.5 | 898 | 1 | 7/7 | correct | 18 UNRESOLVED | exported |

Mean 205.34 s, sample standard deviation 17.20 s. The model produced 898 tokens and the same quotations in all three runs (temperature 0), so the time spread is CPU contention, not different output. Source-span precision was 1.0 in every run: no extra criteria were proposed.

Award history was FOUND in every run and the closing-date discrepancy was recorded each time. Criteria stay manual until a person maps them, so model runs produce 18 UNRESOLVED evidence cells and no price rows. Ollama reported 1,750,576,659 bytes allocated, zero VRAM, 16,384-token context. Hosted API cost: zero.

### Earlier five-run series (11 October 2026, previous graph)

Same model, prompt and inputs; 100.78 s to 193.20 s, mean 141.58 s, sample standard deviation 37.45 s, 7/7 source spans and correct supersession in all five. Combined with the three runs above, eight real Qwen workflows have completed without a validation failure. These are five easy synthetic inputs; they do not show accuracy on long public PDFs.

### How the prompt got here (all real failures, all kept)

- v1: timed out at 120 s on CPU; budgets raised.
- v1: rejected after 190.38 s because display wording paraphrased the source.
- v2: citations in the wrong field, addendum omitted; rejected after 119.72 s.
- v3: invented supersession links; this exposed a missing semantic check, now a regression test (row 3).
- v4: one document per request, supersession allowed only when an addendum quote names the criterion. Current.

## Unfixed failure: scanned pages

`test_scanned_page_ocr_known_failure` builds an image-only certificate page and expects its text. Extraction returns empty text and `OCR_FAILED`. The test is a strict XFAIL, so an accidental pass would fail the suite. Next: sandboxed PDF sanitization, selective OCR (Tesseract) on pages with no native text, rotation handling, and page-level provenance for OCR text, validated on merged tables before claiming support.

## Other limits

- The retry loop has not been triggered by a real model; a weaker prompt or a long public PDF would be the way to observe it.
- Precision and recall on real tender PDFs are unmeasured; the KEMSA portal timed out for every original document.
- Registry checks (Pharmacy and Poisons Board, debarment) never return verified records.
- Human pause time, peak whole-machine memory and electricity are not measured.
- `start.sh` passed under Git Bash on Windows only.

Machine-readable results stay in ignored `outputs/`: `test-results.xml`, `mcp-integration-result.json`, `model-evaluation-result.json` (15 October) and `model-evaluation-result-2026-10-11.json`, with case manifests and logs. Fixtures and assertions are committed in `sample_case/` and `tests/`.
