# Health Commodity Tender Workbench

An agent that prepares the evaluation file for a health commodity tender committee and then stops. It inventories the tender, addenda and bids, compiles the published criteria with exact citations, checks each bid against the criteria a named person has locked, checks price arithmetic, pulls the tender's real award history from Kenya's public OCDS data, and drafts an unsigned report. A named human approves the plan and the export. The agent never selects a winner, signs, or awards.

**Track:** Governance, The Bid Box Challenge. **Theme:** Health commodity tenders. **User:** an ad hoc tender evaluation committee at a buyer like KEMSA (Kenya Medical Supplies Authority) doing preliminary, technical and financial evaluation.

## Which half this is built on

Both, kept separate:

| Half | Data | What it supports |
| --- | --- | --- |
| Bid evaluation | An original **synthetic** tender, addendum and three synthetic bids. Public portals publish no bid documents. | Criteria plan, evidence matrix, price arithmetic, draft file |
| Public record | **Real** Kenya PPRA OCDS releases for 2024 and 2025 (92,229 contracting processes) from the [OCP Data Registry](https://data.open-contracting.org/en/publication/147) | Award history for the reference tender KEMSA/OIT05/2024-2026, comparable awards, closing-date cross-check |

The public data has no item lines (zero tender or award items), so there is **no unit-price benchmark**. Award values are whole-contract amounts and are shown as context, never as a finding against a supplier.

## Run it

Prerequisites: [uv](https://docs.astral.sh/uv/getting-started/installation/) and [Node.js LTS](https://nodejs.org/). Python 3.12 and all packages are pinned (`uv.lock`, `package-lock.json`).

```bash
./scripts/start.sh          # macOS, Linux, Git Bash
```

```powershell
./scripts/start.ps1         # Windows PowerShell
```

The first run downloads about 16 MB of public OCDS data into ignored `local_data/` and builds a local index (about one minute). Skip it with `--no-public-data` or `-NoPublicData`; award history then reports `SOURCE_UNAVAILABLE` and the rest still runs.

Open **http://127.0.0.1:8000**, choose **Load synthetic case**, then:

1. **Compile evaluation plan.** The agent writes its work plan, compiles the criteria and fetches the award history. Note the closing-date warning.
2. Open citations, then **Review and lock plan** under your own name.
3. **Evaluate synthetic bids.** Inspect the matrix, price checks and review queue.
4. **Approve draft export** under your own name and download the package.

Checks:

```bash
./scripts/start.sh --check                 # or ./scripts/start.ps1 -CheckOnly
uv run python -m scripts.mcp_smoke         # full agent run over real MCP stdio transport
```

## How the agent works

LangGraph runs these nodes ([orchestrator/workflow.py](orchestrator/workflow.py)):

1. **inspect**: reads the case manifest through the borrowed Filesystem MCP server and writes a work plan with reasons to the audit log. If the borrowed server is down, it plans from the local store and records that.
2. **compile**: calls `compile_evaluation_plan`. With a local model, a rejected proposal (for example a quotation that is not on the cited page) is retried up to three times, and each retry receives the validator's error. After the limit the agent stops in `HUMAN_RECOVERY_REQUIRED`; it never invents criteria.
3. **award_history** (only when a reference OCID is linked): calls `search_award_history` and compares the declared closing date with the published one.
4. **named plan approval**: pauses until a person locks the exact plan digest.
5. **evaluate** then **draft**: evidence matrix, price checks, unsigned package.
6. **named export approval**: pauses until a person approves the exact draft digest.

The planner is rule-based on purpose. A 1.5B local model is not reliable enough to choose tools, and a rule leaves a readable reason in the log.

### MCP tools

Built ([mcp_server/server.py](mcp_server/server.py), stdio):

| Tool | Does |
| --- | --- |
| `register_case` | Hashes and extracts every document; writes the versioned manifest |
| `compile_evaluation_plan` | Writes a draft plan whose every criterion quotes its source page; accepts validator feedback for retries |
| `search_award_history` | Searches Kenya OCDS by OCID or keywords; returns cited awards with data-quality flags; with a case, saves a cited annex |
| `evaluate_bid_pack` | Writes the evidence matrix and price observations against the locked plan only |
| `draft_evaluation_file` | Writes the unsigned report, CSV matrix, JSON evidence, award history annex and review queue |

Approval is deliberately not an MCP tool. Only the local UI can lock a plan or approve export.

Borrowed: the official [`@modelcontextprotocol/server-filesystem`](https://www.npmjs.com/package/@modelcontextprotocol/server-filesystem) `read_text_file`, scoped to one case folder. Its path validation is already reviewed and maintained; writing our own file server would add risk for no gain.

### Messy public data, handled

The registry documents the defects; the tool flags them rather than cleaning them silently:

- Supplier names with list numbers (`"17.\tLaboratory & Allied Ltd"`): normalized, published name kept, flagged.
- Zero, missing, or top-1% award values: flagged and excluded from statistics, still shown.
- Tender periods whose start is after their end: flagged.
- Supplier identifiers use the portal's internal `Bidders` scheme, so they cannot prove legal identity. No identity matching is attempted.
- Parties carry personal contact details. They are dropped at index time and never stored.

Every value cites the source file SHA-256, line number, OCID, release ID and JSON pointer.

## Open-weights model

Qwen2.5-1.5B-Instruct Q4_K_M (Apache 2.0, publisher checksum verified) served by Ollama on CPU. Windows setup: `./scripts/start.ps1 -WithOllama`, then enter `tender-qwen:1.5b-q4` in the extraction settings. On macOS or Linux, install Ollama, import or pull a Qwen model, and set `TENDER_LOCAL_MODEL_URL`. Details: [docs/MODEL_SETUP.md](docs/MODEL_SETUP.md).

The model only proposes criteria with quotations. Code verifies each quotation against the page, binds the document hash, and keeps every method manual until a person maps it. Arithmetic and approvals never go to the model.

## Measured results

See [EVALS.md](EVALS.md). Summary as of 15 October 2026:

- Test suite: **49 passed, 1 expected failure** (scanned-page OCR).
- Full agent run over real MCP transport with real OCDS data, four repeats: 5 custom tools plus the borrowed server, 18 cited evidence cells, 9 price rows, 1 closing-date discrepancy cited to the OCDS record, audit chain valid, 29.89 to 56.27 seconds, identical results.
- Three Qwen workflows through this graph: all exported, 7/7 gold source spans, correct addendum precedence, first-attempt success, 193.06 to 225.00 seconds (119.5 to 156.0 s of model inference, 898 identical output tokens each). Five earlier runs on 11 October: 100.78 to 193.20 seconds.
- The retry loop is covered by tests with a deliberately wrong simulated model; Qwen has not yet failed validation in a real run, so the loop has not been observed live.
- Cost per run: no hosted API. CPU time on a 16 GB laptop; electricity not measured.

## Not finished

- **No OCR.** Image-only pages become `OCR_FAILED` and stay unresolved (a strict expected-failure test).
- **Real tender PDFs not used.** The KEMSA portal timed out for the original and both addenda. The closing date is now cross-checked against OCDS (archive page 12 November 2024, OCDS 13 November 2024) and left for a human to resolve.
- **No unit-price benchmark.** The public data has no item lines.
- **Registry checks are stubs.** Pharmacy and Poisons Board and debarment lookups stay `UNRESOLVED`; no verified records are parsed.
- **Practitioner review pending.** The workflow has not yet been reviewed by a working procurement officer.
- **Stronger-model comparison not done.**
- **`start.sh` is tested under Git Bash on Windows only**, not on macOS or Linux.
- Reviewer names are local attestations, not authentication. Graph checkpoints are in memory; case state in SQLite rebuilds the gates after a restart.

## Data and licence

Code: MIT. Bids, criteria and products in `sample_case/` are original synthetic fixtures, not transcriptions of any real tender. OCDS data is downloaded at setup and never committed; the registry lists no licence for this publication. Never use a live tender or personal details. Ignored folders: `local_data/`, `models/`, `.runtime/`, `outputs/`, `.env`.

More: [ARCHITECTURE.md](ARCHITECTURE.md), [EVALS.md](EVALS.md), [tool contracts](docs/TOOL_CONTRACTS.md), [reference case](docs/REFERENCE_CASE.md), [submission text](docs/SUBMISSION.md).
