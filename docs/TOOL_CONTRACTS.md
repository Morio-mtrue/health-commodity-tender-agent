# MCP tool contracts

All four tools are implemented in mcp_server/server.py and exercised through actual stdio transport. This document describes the intended contract; README.md records current limitations. Human approvals are local UI attestations and are deliberately absent from the MCP tool surface.

## Shared rules

Every call receives a unique call ID and records UTC start/end timestamps, tool/version, validated inputs, sanitized outputs, status, duration, and explicit error details. The UI presents local times in Africa/Nairobi. Audit entries link to the relevant case, manifest, plan revision, and run. Failed calls are logged too. Secrets are never included in logs.

Case IDs are generated identifiers, not arbitrary paths. Files are confined to one resolved case root. Inputs cannot create executable instructions from document text. Sources include document SHA-256, document ID, 1-based page, section, exact evidence text, and optional bounding box/table coordinates. External sources additionally include URL, retrieval timestamp, data-as-of date, and archived response hash where permitted.

Only human UI approval operations can lock criteria and approve export. A tool accepting a reviewer label cannot treat that label as evidence of an approval.

## register_case

**Inputs:** case name, operator label, tender file references, addendum references and precedence links, synthetic bidder file groups, declared closed-tender provenance.

**Outputs:** case ID, versioned manifest, document hashes/types/pages, synthetic labels, relationships, validation warnings, and failed-document queue.

**Effects:** creates case-local inventory and an audit event. Unreadable or disallowed inputs cannot become trusted evidence. Registration cannot evaluate bids or issue a plan approval.

## compile_evaluation_plan

**Inputs:** case ID, current manifest ID, bounded extraction settings.

**Outputs:** draft plan ID/hash/revision, ordered stage criteria, exact source wording, published mandatory/weighted rules, expected evidence, extraction uncertainty, and unresolved requirements.

**Effects:** saves a versioned draft. Each active criterion must cite an applicable tender/addendum passage. Unsupported proposed rules remain unresolved rather than active criteria. A named human review and lock are required before evaluation.

## evaluate_bid_pack

**Inputs:** case ID, locked plan ID/hash, selected bidder ID(s), run configuration.

**Outputs:** bidder-by-criterion evidence cells, supported calculations, submitted-price values, calculated-price observations, source-check results, and unresolved items.

**Effects:** creates a versioned evaluation result. Reject unapproved/stale plans and changed source hashes. Only locked criteria may affect compliance. Lack of a portal match is unresolved. New findings require validated citations and calculation references where applicable.

## draft_evaluation_file

**Inputs:** case ID, locked plan hash, compatible evaluation run IDs, requested review package format.

**Outputs:** draft ID/hash, unsigned report, matrix, evidence ledger, price observations, exception queue, and audit export.

**Effects:** creates case-local draft artifacts for inspection. Requires coherent input versions and finding provenance. It never recommends an award or signs a report. Export of the approved package is a separate named human gate tied to this draft hash.

## Workflow states

`CASE_CREATED` → `FILES_VALIDATED` → `PLAN_DRAFTED` → `WAITING_FOR_PLAN_APPROVAL` → `PLAN_LOCKED` → `BIDS_EXTRACTED` → `CHECKS_COMPLETED` → `FINDINGS_VERIFIED` → `DRAFT_READY` → `WAITING_FOR_EXPORT_APPROVAL` → `EXPORTED`.

Explicit failure/review reasons: `MISSING_DOCUMENT`, `OCR_FAILED`, `SOURCE_UNAVAILABLE`, `AMBIGUOUS_EVIDENCE`, `CALCULATION_CONFLICT`, and `HUMAN_REVIEW_REQUIRED`. An unavailable external source may allow drafting with a cited unresolved item; an unapproved plan blocks evaluation.
