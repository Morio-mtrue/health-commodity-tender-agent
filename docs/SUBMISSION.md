# Submission text and recording guide

## Description (about 300 words)

Health Commodity Tender Workbench prepares the evaluation file for a public tender evaluation committee buying medicines, the work a Kenya Medical Supplies Authority (KEMSA) ad hoc committee does in its preliminary, technical and financial evaluation. Theme: Health commodity tenders. It never selects a supplier, signs, or awards.

A LangGraph agent reads the case manifest through the official Filesystem MCP server and writes a work plan with reasons. It then calls five tools on our own MCP server: register_case, compile_evaluation_plan, search_award_history, evaluate_bid_pack and draft_evaluation_file. If a local model's criteria proposal fails validation, for example a quotation that is not on the cited page, the agent retries with the validator's error and stops for a named human after three attempts. Two interrupts require a named person to lock the exact plan digest and to approve the exact draft. Every tool call, retry, decision and approval goes to a hash-chained audit log.

Bid documents are not public, so the bid half runs on an original synthetic tender, addendum and three synthetic bids. Every criterion quotes its source page; every finding cites a document hash and page; missing or ambiguous evidence stays unresolved; submitted prices are preserved while Decimal arithmetic exposes discrepancies.

The public half runs on real Kenya PPRA OCDS data for 2024 and 2025. For the reference tender KEMSA/OIT05/2024-2026 the agent retrieves eight awards worth KES 45.2 million and reports that the archive page (12 November 2024) and the OCDS record (13 November 2024) disagree on the closing date, citing file hash, line and JSON pointer. It flags numbered supplier names, zero and extreme values, and inverted tender periods, and drops personal contact details. The data has no item lines, so no unit-price benchmark is claimed.

Criteria extraction runs on Qwen2.5-1.5B through Ollama on a CPU laptop. Unfinished: OCR, registry lookups, real tender PDFs, practitioner review, and a stronger-model comparison.

## Recording plan (under 3 minutes, unedited)

The model compile takes about 2 to 4 minutes on this laptop, longer than the whole video. So the live run uses the structured synthetic case, and the open-weights run is shown from its completed case and log. Say this on camera.

Before recording:

1. `./scripts/start.ps1` (or `start.sh`) running in a visible terminal.
2. Run `uv run python -m scripts.prepare_failure_case` so the "expected stop" case exists.
3. Have one completed Qwen case in the picker: with the project Ollama running (`./scripts/start.ps1 -WithOllama` starts it on port 11435), set `TENDER_LOCAL_MODEL_URL=http://127.0.0.1:11435` and run `uv run python -m scripts.prepare_model_review`. Then lock and export that case yourself under your own name.
4. Browser at http://127.0.0.1:8000, zoom so tables are readable.

Sequence (target times):

| Time | Show | Say |
| --- | --- | --- |
| 0:00 | Landing page | Who it is for; it prepares the file and stops; it never awards. |
| 0:15 | Load synthetic case, Case files | Every document hashed; bids are synthetic. |
| 0:25 | Compile evaluation plan, then Case files: Agent work plan | Manifest read via the borrowed Filesystem MCP; steps chosen with reasons. |
| 0:45 | Evaluation plan: closing-date warning, open one citation | Real OCDS record says 13 November, archive says 12; the agent flags it and does not choose. |
| 1:05 | Review and lock plan, type your own name | Lock binds this exact digest. |
| 1:15 | Evaluate, Compliance matrix, open BID_B P02 and the price row | Cited absence; 59,000 submitted, 60,000 calculated, submitted value preserved. |
| 1:40 | Review queue: Public award history | Eight real awards, flags for numbered supplier names, file and line citations, no unit-price claim. |
| 2:00 | Approve draft export with your name, then Audit trail | Every MCP call with inputs, outputs and timestamps; hash chain verified. |
| 2:20 | Case picker: completed Qwen case, its audit trail | Open-weights run: model digest, timings, quotation checks. |
| 2:35 | Case picker: expected-stop case | Where it fails: native tender, no model, agent stops for a human instead of inventing criteria. No OCR either. |
| 2:50 | End | Repository link. |

Do not cut processing time out and still call it unedited. If you overrun, drop the Qwen case segment and mention it in the description.

## Links to fill

- Code: https://github.com/Morio-mtrue/health-commodity-tender-agent
- Video: pending recording
- Practitioner conversation: pending
