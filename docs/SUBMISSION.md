# Submission draft and recording guide

This is a reviewable draft. Repository publication is authorized and complete; no competition form, practitioner message, or video publication has been submitted.

## Description (300 whitespace-delimited words)

Health Commodity Tender Evaluation Workbench helps a public sector committee review a closed health commodity tender using clearly labelled synthetic bids. It preserves original documents, hashes every source, extracts published requirements, and prepares an unsigned evaluation package for human review. It never selects a supplier, issues an award, changes submitted prices, or contacts bidders.

A bounded LangGraph workflow invokes four custom MCP tools over actual stdio transport: register_case, compile_evaluation_plan, evaluate_bid_pack, and draft_evaluation_file. The official Filesystem MCP server reads the active case manifest inside a restricted case directory. Every tool call records inputs, outputs, timing, status, and errors in a hash linked audit trail.

Local Qwen weights run through signed Ollama on the Windows demo computer. Schema constrained extraction proposes manual criteria with quotations. The application verifies each quotation against its original page and binds the source hash from the trusted manifest. A named reviewer checks completeness, addendum precedence, and deterministic mappings before locking the exact plan digest. A separate named approval binds export to the reviewed draft digest.

Deterministic code uses Decimal arithmetic for extended prices, pack normalization, rounding, and explicitly sourced currency conversion. It preserves submitted amounts and records discrepancies. Ambiguous equivalents, inaccessible portals, corrupt documents, and missing interpretation remain unresolved. Exports include the evidence matrix, original sources, price observations, review queue, approval records, raw model proposal, and complete tool logs; recommendation and signature fields stay blank.

Tests exercise addendum precedence, missing certificates, price discrepancies, expiry observations, prompt injection, changed sources, stale approvals, and path boundaries. A real scanned fixture exposes the current OCR limitation. The selected closed KEMSA reference still requires retrieval and closing date reconciliation. Public register parsing and a stronger model comparison remain unfinished. Automated TEST SIMULATION approvals measure engineering behavior; practitioner review and actual human approvals are required before the public demonstration and final submission.

## Before recording

- Obtain the selected public originals and all addenda, reconcile the closing date, and freeze actual schedule lines.
- Have the arranged practitioner review completeness, terminology, deterministic mappings, and gold labels using REVIEW_CHECKLIST.md.
- Perform the plan and export approvals yourself, under your own name.
- Confirm the current model measurements in EVALS.md. Simulated test gates are not human committee approvals.
- Use synthetic supplier names, registrations, certificates, and prices throughout. Keep real contact details out of the recording and public fixtures.

## Unedited recording sequence

1. Start the local workbench and model before recording. Display the closed-tender provenance and clearly labelled synthetic bid inventory.
2. Compile the plan with the exact pinned local model tag. Keep recording during inference; explain the four MCP tools, borrowed server, source hashes, and review gates while the model runs.
3. Open a quotation and its full source page. Show the addendum link and check completeness. Lock the reviewed plan with your own name and exact digest.
4. Evaluate and show the cited matrix, preserved submitted price discrepancy, and unresolved reference checks.
5. Open the unsigned draft. Show blank recommendation/signature/award fields. Approve export yourself and show the package and complete audit.

The public video must be under three minutes and show an unedited run. Rehearse against actual measured latency; if model compilation and necessary review cannot fit, reduce the coherent tender excerpt or select a tested faster model. Do not cut out processing or human gates and describe the result as unedited. A video is not generated or uploaded by this project.

## Submission links to fill

- Code: https://github.com/Morio-mtrue/health-commodity-tender-agent
- Public video: pending user recording and publication
- Practitioner review: pending
- Selected public corpus and complete source provenance: pending originals
- Organizer eligibility/build window: user waived the local prerequisite; organizer certification remains unverified
