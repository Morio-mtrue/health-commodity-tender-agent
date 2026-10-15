"""Run the local model on real pages of the closed KEMSA/OIT05/2024-2026 tender.

Needs the public original in local_data/ (the PPIP mirror; the KEMSA site timed out) and the project
Ollama on port 11435. Pages 39 to 44 hold the published evaluation criteria. Bids stay synthetic.
The run stops at the named plan gate; no approval is simulated.

TENDER_LOCAL_MODEL_URL=http://127.0.0.1:11435 uv run python -m scripts.real_tender_run
"""
import asyncio
import base64
import io
import json
import time
from pathlib import Path

from pypdf import PdfReader, PdfWriter

from orchestrator.mcp_client import procurement
from orchestrator.store import Store, file_hash, now
from orchestrator.workflow import Workflow
from sample_case.fixture import request

ORIGINAL = Path("local_data/kemsa-oit05-2024-2026/original-ppip.pdf")
SOURCE = "https://tenders.go.ke/storage/Documents/1728986416665-supply-of-health-products-liquid-dosage-forms-inhalation-products-and-topical-formulations.pdf"
FIRST, LAST = 39, 44


def excerpt():
    reader, writer = PdfReader(ORIGINAL), PdfWriter()
    for number in range(FIRST, LAST + 1):
        writer.add_page(reader.pages[number - 1])
    buffer = io.BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


async def main(model="tender-qwen:1.5b-q4"):
    store = Store("outputs/real-tender")
    payload = request("Demo operator")
    bids = [d for d in payload["documents"] if d["kind"] == "bid"]
    tender = {"name": f"kemsa-oit05-pages-{FIRST}-{LAST}.pdf", "kind": "tender", "synthetic": False, "source_url": SOURCE,
              "content_base64": base64.b64encode(excerpt()).decode()}
    payload.update(name="KEMSA/OIT05/2024-2026 real criteria pages, synthetic bids", documents=[tender, *bids],
                   closed_on="2024-11-13", reference_ocid="ocds-5whusi-KEMSA/OIT05/2024-2026",
                   closure_source=f"OCDS tenderPeriod.endDate; original PDF SHA-256 {file_hash(ORIGINAL)}, pages {FIRST} to {LAST}")
    started = time.monotonic()
    case = await procurement(store, "register_case", {"request": payload})
    case = await Workflow(store).advance(case["id"], model=model)
    recovery = [{"status": e["status"], "error": e["outputs"]["error"][:300]} for e in store.events(case["id"]) if e["tool"] == "agent.recovery"]
    plan = case.get("plan") or {}
    result = {"timestamp": now(), "case_id": case["id"], "state": case["state"], "model": model,
              "original_sha256": file_hash(ORIGINAL), "pages": [FIRST, LAST],
              "excerpt_chars": sum(len(p["text"]) for p in case["documents"][0]["extraction"]["pages"]),
              "attempts": 1 + sum(r["status"] == "RETRY" for r in recovery), "recovery_events": recovery,
              "criteria": len(plan.get("criteria", [])),
              "criteria_detail": [{"id": c["id"], "stage": c["stage"], "page": c["source"]["page"] + FIRST - 1,
                                   "quote": c["source"]["quote"][:160]} for c in plan.get("criteria", [])],
              "model_run": {k: case.get("model_run", {}).get(k) for k in ("total_duration_ns", "prompt_eval_count", "eval_count", "model_digest")},
              "award_history": (case.get("award_history") or {}).get("observations"),
              "duration_seconds": round(time.monotonic() - started, 2), "audit_integrity": store.verify_audit()}
    Path("outputs/real-tender-result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "criteria_detail"}, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
