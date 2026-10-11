# Health Commodity Tender Evaluation Agent — Build Plan

## 1. Executive summary

Build a local, evidence-first evaluation workbench for a public-sector health commodity tender committee. The agent will take a **closed tender**, its addenda, and a set of **synthetic bids**; extract and lock the tender's published evaluation criteria; build a cited compliance matrix; run deterministic financial and health-product checks; and prepare an unsigned draft evaluation file for a human committee.

The agent will **not award a tender, select a winner, alter a bid, introduce evaluation criteria, or make unsupported adverse claims about a supplier**.

The hackathon version should optimize for auditability, reliability, and a complete live run—not breadth. Four dependable MCP tools are better than a large collection of shallow integrations.

## 2. Challenge fit

### Target track and theme

- Track: Governance — The Bid Box Challenge
- Theme: Health & life sciences — Health commodity tenders
- Intended user: a KEMSA-style ad hoc tender evaluation committee
- Workflow: preliminary, technical, and financial evaluation of bids for health products
- Human decision-maker: the evaluation committee and accounting officer

### Mandatory challenge requirements

- [ ] Create a custom MCP server with at least three distinct tools.
- [ ] Ensure at least one custom tool creates a useful artifact, flag, or file.
- [ ] Use at least one MCP server the team did not write.
- [ ] Use open-source orchestration.
- [ ] Complete one full workflow using an open-weights model.
- [ ] Log every tool call with inputs, outputs, timestamps, and status.
- [ ] Gate every consequential or irreversible action with a named human approver.
- [ ] Ensure every finding cites its source.
- [ ] Keep the award decision outside the agent.
- [ ] Publish the code under an OSI-approved licence.
- [ ] Provide a one-command local setup.
- [ ] Record a public demo video under three minutes showing an unedited run.
- [ ] Include a one-page `ARCHITECTURE.md`.
- [ ] Include `EVALS.md` with at least eight test tasks, pass/fail results, and one unresolved failure.
- [ ] Use only closed public tenders and synthetic or properly authorized data.
- [ ] Do not use personal details or a live tender in progress.
- [ ] Keep the implementation within the official build window.

### Immediate organizer clarification

The official pages conflict on a five-day versus seven-day build period, while the stated submission deadline is 15 October 2026. Before implementation begins, obtain a public written clarification of the official build-start timestamp. Repository scaffolding may be created beforehand, but implementation outside the permitted window could disqualify the entry.

## 3. Product definition

### Product promise

> Turn a closed health-commodity tender and synthetic bid pack into a committee-ready, source-cited evaluation file in under 20 minutes, while preserving human judgment and a complete audit trail.

### Primary user outcome

The committee receives:

1. a versioned manifest of all tender, addendum, and bid files;
2. a human-approved evaluation plan derived from the tender;
3. a bidder-by-criterion compliance matrix;
4. deterministic arithmetic and unit-price checks;
5. health-product validation and benchmark observations;
6. an unresolved-evidence queue;
7. an unsigned draft evaluation report; and
8. a readable tool and approval log.

### Non-goals

The hackathon product will not:

- evaluate a live procurement;
- ingest real unpublished bids;
- recommend or issue an award;
- send communications to bidders;
- change a submitted tender price;
- perform autonomous due diligence using private data;
- integrate directly with KHIS, KEMSA LMIS, or e-GP;
- create a generic supplier risk score;
- use fuzzy-name matching as grounds for an adverse finding;
- perform nationwide consumption forecasting;
- claim production readiness.

## 4. Scope decision

### Recommended demonstration case

Use a small excerpt from a **closed KEMSA oral-formulations tender**, including any relevant addendum or clarification. Limit the case to three to five health-product line items and create three to five synthetic bidders.

This case supports meaningful checks for:

- active ingredient or generic name;
- strength;
- dosage form;
- unit of issue and pack size;
- quantity offered;
- shelf-life and storage evidence;
- PPB product registration;
- mandatory tender documents;
- unit and extended price arithmetic; and
- price comparison after unit normalization.

### Two workflows that must remain separate

#### A. Bid evaluation — in scope

Apply only criteria and procedures found in the tender and its valid addenda. Produce evidence and calculations for committee review.

#### B. Procurement-plan or tender-design QA — optional/post-hackathon

Before a tender is advertised, compare proposed quantities and specifications with KEML/KEMSL, consumption, stock, lead time, and price benchmarks. These observations must not be retroactively introduced into bid evaluation unless the published tender made them evaluation criteria.

## 5. User workflow

1. **Create case**
   - The user selects a closed tender, addenda, clarifications, and synthetic bid folders.
   - The system validates file types, hashes each file, and creates a manifest.

2. **Compile evaluation plan**
   - The agent extracts preliminary, technical, financial, and due-diligence criteria.
   - Every criterion includes source document, page, section, exact text, type, and expected evidence.

3. **Human criteria lock**
   - A named reviewer approves or edits the proposed plan.
   - No bid can be evaluated until this plan is locked.

4. **Extract bid evidence**
   - Native PDF text is used first.
   - OCR is used only for scanned pages.
   - Tables are extracted with page and cell coordinates when possible.

5. **Evaluate and calculate**
   - The agent maps submitted evidence to locked criteria.
   - Deterministic code performs arithmetic, date, currency, and unit conversions.

6. **Run external checks**
   - PPB product registration.
   - PPRA debarment list.
   - KEML/KEMSL terminology or level-of-care reference.
   - PPRA market-price reference, when comparable.

7. **Verify findings**
   - Every adverse or unresolved finding must have a source.
   - A failed lookup becomes `UNRESOLVED`, not automatic noncompliance.

8. **Draft evaluation file**
   - Generate the matrix, exception queue, evaluated-price table, and report draft.
   - Leave committee recommendation, signatures, and award decision blank.

9. **Human finalization gate**
   - A named reviewer approves export of the draft package.
   - The approval is logged but does not represent an award.

## 6. Architecture

### Design principle

Use one bounded state graph instead of a conversational multi-agent swarm. Agentic depth comes from planning, tool use, validation, recovery, and human gates—not from the number of agents.

### Components

1. **Simple local UI**
   - Upload/select documents.
   - Review and lock criteria.
   - Inspect citations and unresolved items.
   - Approve draft export.

2. **Open-source orchestrator**
   - LangGraph or Pydantic AI.
   - Explicit states and transitions.
   - Bounded retry policies.

3. **Custom procurement MCP server**
   - Case registration.
   - Evaluation-plan compilation.
   - Bid-pack evaluation.
   - Report drafting.

4. **Borrowed MCP server**
   - Recommended: official Filesystem MCP restricted to the case workspace.
   - Reason: mature, reusable path-scoped file operations are safer than a custom file layer.

5. **Document pipeline**
   - Native PDF extraction first.
   - OCR fallback per page.
   - Table extraction.
   - Page-level provenance.

6. **Deterministic rules engine**
   - Arithmetic and totals.
   - Date and validity checks.
   - Unit and pack normalization.
   - Currency conversion using the tender-specified rule.
   - Locked mandatory gates and weighted scoring.

7. **Local evidence store**
   - SQLite or DuckDB plus JSON artifacts.
   - Immutable audit events.
   - Document hashes and version relationships.

8. **Local open-weights model**
   - Use for extraction, normalization, and concise explanations.
   - Recommended starting candidates: quantized Gemma 4 12B Unified if hardware permits; otherwise an effective-parameter 4B variant.
   - Run a small bake-off on the actual demo machine before locking the model.

### State graph

`CASE_CREATED` → `FILES_VALIDATED` → `PLAN_DRAFTED` → `WAITING_FOR_PLAN_APPROVAL` → `PLAN_LOCKED` → `BIDS_EXTRACTED` → `CHECKS_COMPLETED` → `FINDINGS_VERIFIED` → `DRAFT_READY` → `WAITING_FOR_EXPORT_APPROVAL` → `EXPORTED`

Failure states should be explicit:

- `MISSING_DOCUMENT`
- `OCR_FAILED`
- `SOURCE_UNAVAILABLE`
- `AMBIGUOUS_EVIDENCE`
- `CALCULATION_CONFLICT`
- `HUMAN_REVIEW_REQUIRED`

## 7. Custom MCP tool design

### Tool 1: `register_case`

**Purpose:** Create a trusted inventory of the evaluation case.

**Inputs:** case name, tender files, addenda, bid folders, operator name.

**Outputs:** case ID, file manifest, hashes, document types, version/addendum relationships, validation warnings.

**Writes:** case manifest and audit event.

### Tool 2: `compile_evaluation_plan`

**Purpose:** Convert the tender and addenda into a structured evaluation plan.

**Inputs:** case ID and optional extraction settings.

**Outputs:** ordered criteria grouped into preliminary, technical, financial, and due-diligence stages.

**Important control:** output remains a draft until a named human locks it.

### Tool 3: `evaluate_bid_pack`

**Purpose:** Map evidence from each bid to the locked evaluation plan and run deterministic checks.

**Inputs:** case ID, locked plan ID, bidder folder.

**Outputs:** compliance matrix, cited evidence, calculations, external-check results, and unresolved items.

**Important control:** only locked criteria may affect status or calculation.

### Tool 4: `draft_evaluation_file`

**Purpose:** Create the committee review package.

**Inputs:** case ID, evaluated bidder results, named reviewer.

**Outputs:** unsigned draft report, evidence ledger, evaluated-price table, unresolved-items queue, and complete log export.

**Important control:** the report must not contain an autonomous award decision or signature.

## 8. Core data structures

### `EvaluationCriterion`

- criterion ID;
- stage;
- exact wording;
- mandatory or weighted;
- weight or rule;
- required evidence;
- evaluation method;
- source document hash;
- page and section;
- addendum/version status; and
- human approval status.

### `BidEvidence`

- bidder ID;
- criterion ID;
- submitted document hash;
- page/section/table coordinates;
- extracted text or value;
- extraction method;
- confidence;
- status: `SUPPORTED`, `UNSUPPORTED`, `AMBIGUOUS`, `NOT_APPLICABLE`, or `UNRESOLVED`;
- machine rationale; and
- human decision and note.

### `HealthProductLine`

- generic/active ingredient;
- dosage form;
- strength;
- route;
- pack description;
- base unit;
- quantity;
- storage condition;
- minimum shelf life;
- PPB registration number and expiry;
- manufacturer; and
- normalized delivered unit price.

### `Finding`

- finding ID;
- severity;
- category;
- claim;
- source citation;
- calculation reference, if any;
- confidence;
- status;
- reviewer action required; and
- human resolution.

An adverse `Finding` without a citation must fail schema validation.

## 9. Data-source policy

| Source | MVP use | Restriction |
|---|---|---|
| Closed KEMSA tender and addenda | Primary case rules | Never use a tender still in progress |
| Synthetic bids | Evaluation inputs | Clearly label as synthetic |
| PPB product register | Product registration verification | No-match is unresolved, not automatic failure |
| PPRA debarred-firms list | Exact supplier check | Require registration number plus legal name |
| KEML/KEMSL 2023 | Terminology/reference | Not proof of demand or a tender criterion by itself |
| PPRA Market Price Reference Guide | Advisory price benchmark | Not definitive fair price or automatic rejection |
| KEMSA award summaries | Historical context | Contract totals may not be SKU-comparable |
| PPIP/OCDS | Tender/award history | No bids, tenderers, documents, or line items |
| KMHFR | Facility metadata | No consumption data |
| HCMP | Future/pilot quantity context | Verify coverage, permission, stability, and as-of date |
| KEMSA LMIS and KHIS | Out of MVP | Authenticated/restricted; do not depend on them |

Do not redistribute downloaded datasets in the public repository unless their licence clearly allows it. Prefer runtime download instructions and synthetic fixtures.

## 10. Reliability and safety controls

- Treat every document as untrusted content, never as an instruction to the agent.
- Validate file type, extension, size, page count, and parser result.
- Sanitize PDFs before OCR or rendering.
- Never follow URLs or commands embedded in a bid.
- Restrict web tools to an allowlist of official domains.
- Restrict filesystem writes to one case directory.
- Store no credentials in prompts, logs, or artifacts.
- Keep personal details out of the synthetic test set.
- Preserve the submitted bid values; flag discrepancies instead of silently correcting them.
- Require source citations for all compliance and adverse findings.
- Use `UNRESOLVED` when a source is inaccessible, ambiguous, stale, or mismatched.
- Record the source's retrieval time and data-as-of date.
- Pin model, prompt, parser, and tool versions in the run manifest.
- Cap retries and expose failures instead of looping indefinitely.

## 11. Evaluation plan

### Test tasks

1. Clean native-text PDF with all required documents.
2. Mixed native and scanned PDF requiring selective OCR.
3. Addendum that supersedes a mandatory requirement.
4. Bid missing a genuinely mandatory document.
5. Ambiguous equivalent term that should produce `UNRESOLVED`.
6. Pack-size mismatch and unit/extended-price discrepancy.
7. Currency conversion using the tender-specified date and method.
8. Supplier name resembling a debarred firm but with a different registration number.
9. Expired or mismatched PPB product registration.
10. Prompt injection embedded in a bid document.
11. Missing page or corrupted attachment.
12. The same task repeated five times to measure model variation.

### Metrics

- mandatory-criterion extraction recall;
- evidence-cell precision and recall;
- citation/page accuracy;
- numerical accuracy;
- false adverse-flag count;
- correct abstention rate;
- run-to-run agreement;
- completion time;
- cost per run;
- percentage of findings with complete provenance;
- unauthorized tool or write attempts; and
- human corrections required per case.

### Acceptance conditions

- 100% arithmetic correctness.
- Zero unsourced adverse findings.
- Zero autonomous award decisions.
- Zero writes outside the case workspace.
- Every mandatory criterion represented or marked unresolved.
- Complete end-to-end run in less than 20 minutes.
- A reviewer can trace every report finding to its source.
- The complete run can be reproduced from the case manifest.

### Required unresolved failure

Reserve at least one difficult document—such as a badly scanned merged table, handwriting, rotated page, or nonstandard certificate. Report the observed failure honestly in `EVALS.md`; do not fabricate a failure and do not claim it is fixed if it is not.

## 12. Seven-day build sequence

Adjust this only after the organizers confirm the official window.

### Day 1 — Freeze scope and corpus

- Confirm challenge timing and repository rules.
- Select the closed KEMSA tender and three to five line items.
- Create three to five synthetic bids with known success, failure, and ambiguity cases.
- Ask one procurement or pharmaceutical supply-chain practitioner to review the workflow and labels.
- Freeze schemas, non-goals, and acceptance criteria.

**Exit condition:** one written problem statement, one corpus, and one gold evaluation plan.

### Day 2 — Case ingestion and criteria compiler

- Build `register_case`.
- Implement hashing, file inventory, addendum relationships, and audit events.
- Build the first version of `compile_evaluation_plan`.
- Implement criteria-review and lock flow.

**Exit condition:** the system produces a sourced, human-lockable plan from the chosen tender.

### Day 3 — Bid evidence and deterministic checks

- Implement native extraction, selective OCR, and table handling.
- Build `evaluate_bid_pack`.
- Implement compliance states and page citations.
- Add arithmetic, pack, quantity, date, and unit normalization.

**Exit condition:** one synthetic bid is evaluated end to end with traceable evidence.

### Day 4 — External validation and recovery

- Add PPB and PPRA debarment checks.
- Add KEML/KEMSL reference mapping and optional PPRA price benchmark.
- Implement timeouts, retries, domain allowlists, and `UNRESOLVED` behavior.
- Add injection and malformed-document tests.

**Exit condition:** external failures degrade safely and never become unsupported adverse findings.

### Day 5 — Report, open model, and full workflow

- Build `draft_evaluation_file`.
- Add approval gates and named reviewer logs.
- Complete the full task using the chosen open-weights model.
- Measure duration, memory, and cost.

**Exit condition:** a full case completes in less than 20 minutes and produces the review package.

### Day 6 — Evaluation and documentation

- Run at least eight tests; target all twelve.
- Repeat the main run five times.
- Compare open-model and optional frontier-model results.
- Record real pass/fail results and one unresolved failure.
- Write `README.md`, `ARCHITECTURE.md`, and `EVALS.md`.
- Test one-command setup from a clean environment.

**Exit condition:** a stranger can clone, run, and understand the system.

### Day 7 — Demo and submission

- Rehearse the three-minute unedited run.
- Rehearse the 20-minute technical review.
- Practice adding a new evaluation criterion through the locked schema rather than changing prompts.
- Record the final video with tool calls visible.
- Verify licences, links, public visibility, and submission text.
- Freeze the repository before the deadline.

**Exit condition:** all submission artifacts are public, reproducible, and consistent with the actual implementation.

## 13. Suggested repository structure

```text
project/
├── README.md
├── ARCHITECTURE.md
├── EVALS.md
├── LICENSE
├── Makefile or task runner
├── docker-compose.yml or equivalent one-command setup
├── app/                       # Local review UI
├── orchestrator/              # State graph and workflow policies
├── mcp_server/                # Custom procurement MCP server
│   ├── case_tools/
│   ├── evaluation_tools/
│   ├── report_tools/
│   └── schemas/
├── document_pipeline/         # PDF, OCR, and table extraction
├── rules/                     # Deterministic calculations and gates
├── connectors/                # Allowlisted public-source adapters
├── prompts/                   # Versioned extraction prompts
├── tests/
│   ├── fixtures/
│   ├── gold/
│   ├── adversarial/
│   └── regression/
├── sample_case/               # Synthetic public demo case
└── outputs/                   # Generated, ignored except examples
```

## 14. Three-minute demo script

### 0:00–0:20 — Problem and guardrail

Show the closed tender and synthetic bids. State that the agent prepares a sourced draft and never awards the tender.

### 0:20–0:45 — Register the case

Run `register_case`. Show document hashes, the addendum relationship, and the audit log.

### 0:45–1:10 — Compile and lock criteria

Run `compile_evaluation_plan`. Open one extracted criterion at its exact source page. Enter the named human approval and lock the plan.

### 1:10–2:10 — Evaluate bids

Run `evaluate_bid_pack`. Show:

- a correctly supported mandatory requirement;
- a missing certificate with a citation;
- an addendum that changes the applicable requirement;
- a pack-size or arithmetic discrepancy; and
- an external lookup that returns `UNRESOLVED` rather than an unsupported failure.

### 2:10–2:40 — Draft the file

Run `draft_evaluation_file`. Show the compliance matrix, exception queue, evaluated-price table, and blank committee recommendation.

### 2:40–3:00 — Reliability proof

Show the tool log, test summary, run time, cost, and one known failure. End by showing that a human remains responsible for the decision.

## 15. Live technical-review preparation

Expect the judges to add a requirement. Demonstrate that the system can:

- add a criterion to the structured plan;
- identify its source or mark it as an externally supplied demo rule;
- require a new human lock;
- rerun only affected checks;
- preserve prior results and audit history; and
- explain exactly which bidder outcomes changed and why.

Do not solve the live change by editing a hidden prompt. The visible schema and dependency graph should make the change understandable.

## 16. Risk register

| Risk | Impact | Mitigation |
|---|---|---|
| Referenced datasets lack bids and line items | Core workflow cannot run on PPIP alone | Use a closed tender plus synthetic bids |
| OCR/table extraction fails | Missing or wrong evidence | Native extraction first, selective OCR, explicit failure state |
| Agent invents a criterion | Legally unsafe evaluation | Human-lock a sourced evaluation plan before bid processing |
| Fuzzy entity match harms a supplier | Serious audit and reputational risk | Require exact identifiers; otherwise unresolved |
| External portal is unavailable | Broken demo | Cache permitted reference fixtures with retrieval metadata and demonstrate fallback |
| Model output varies | Unreliable evaluation | Structured schemas, deterministic rules, repeated-run testing |
| Scope expands into planning, fraud, and forecasting | Incomplete submission | Freeze non-goals and backlog post-hackathon features |
| Real data creates privacy/licensing issues | Disqualification or legal risk | Closed public tender, synthetic bids, no personal details |
| Repository cannot run cleanly | Ineligibility | Test the one-command setup on a clean machine/container |
| Project looks like a chatbot | Low agentic-depth score | Visible state graph, MCP tools, recovery, validation, and artifacts |

## 17. Pre-build decision checklist

- [ ] Organizer has confirmed the official build window.
- [ ] Target institution/workflow is stated in one sentence.
- [ ] At least one practitioner interview is scheduled.
- [ ] Closed tender and addenda are selected.
- [ ] Three to five product lines are selected.
- [ ] Synthetic bidder scenarios and gold labels are defined.
- [ ] Open-source orchestrator is selected.
- [ ] Custom MCP tool boundaries are frozen.
- [ ] Borrowed MCP server is selected and justified.
- [ ] Demo hardware and open-weights model are selected after a bake-off.
- [ ] Human gates and named roles are defined.
- [ ] Data-source allowlist is defined.
- [ ] Repository and data licences are separated correctly.
- [ ] Evaluation metrics and thresholds are frozen before testing.
- [ ] Three-minute demo story is agreed before UI polish begins.

## 18. Definition of done

The project is complete when a new reviewer can clone the repository, run one command, load the included synthetic case, approve the sourced evaluation plan, execute an open-weights agent run, inspect every finding at its source page, export an unsigned draft evaluation package, and reproduce the recorded evaluation results—without the system ever making the award decision.

## 19. Authoritative references

- Challenge homepage: <https://agentic-africa-challenge.lovable.app/>
- Governance track: <https://agentic-africa-challenge.lovable.app/tracks/governance>
- Kenya PPRA OCDS registry: <https://data.open-contracting.org/en/publication/147>
- PPADA resources: <https://ppra.go.ke/ppda/>
- Procurement regulations: <https://new.kenyalaw.org/akn/ke/act/ln/2020/69/eng@2022-12-31/source>
- PPRA standard tender documents: <https://ppra.go.ke/standard-tender-documents/1000/>
- PPRA market-price guide: <https://ppra.go.ke/market-price-index/>
- PPRA debarred firms: <https://ppra.go.ke/debarred-firms/>
- PPRA Review Board decisions: <https://ppra.go.ke/arb-decisions/>
- KEMSA tender archive: <https://kemsa.go.ke/tenders/link>
- KEMSA contracts awarded: <https://kemsa.go.ke/articles/tender-awards>
- KEMSA product catalogue: <https://kemsa.go.ke/content/137/publications/kemsa-product-catalogue>
- KEML/KEMSL downloads: <https://www.kemsa.go.ke/content/135/downloads/other-downloads>
- PPB registered products: <https://products.pharmacyboardkenya.org/ppb_admin/pages/public_view_retention_products.php>
- Kenya Master Health Facility Registry: <https://kmhfr.health.go.ke/public/about>
- KEMSA LMIS: <https://lmis3.kemsa.go.ke/auth/signin>
- KHIS: <https://hiskenya.dha.go.ke/dhis-web-commons/security/login.action>
- Kenya Data Protection Act: <https://new.kenyalaw.org/akn/ke/act/2019/24/eng@2022-12-31/source>
- Official Filesystem MCP: <https://github.com/modelcontextprotocol/servers/blob/main/src/filesystem/README.md>
- Official Fetch MCP: <https://github.com/modelcontextprotocol/servers/blob/main/src/fetch/README.md>

