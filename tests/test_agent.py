"""Agent planning, recovery, and OCDS award history. Approvals here are TEST SIMULATION."""
from __future__ import annotations

import gzip
import json
import sqlite3

import pytest

from connectors.ocds import award_history, build_index
from mcp_server.service import ProcurementService
from orchestrator.store import Store
from orchestrator.workflow import Workflow
from sample_case.fixture import request

REFERENCE = "ocds-5whusi-KEMSA/OIT05/2024-2026"


def release(ocid, title, end, awards, start=None, buyer="Synthetic Buyer"):
    return {"ocid": ocid, "id": ocid + "-r1", "date": "2024-10-15T13:00:16+03:00", "buyer": {"id": "1", "name": buyer},
            "tender": {"title": title, "tenderPeriod": {"startDate": start or "2024-10-15T00:00:00+03:00", "endDate": end},
                       "procurementMethod": "open", "mainProcurementCategory": "goods"},
            "awards": awards,
            # Mirrors the real publication: parties carry personal contact points that must never be indexed.
            "parties": [{"id": "9", "name": "Person Contact Ltd", "roles": ["supplier"],
                         "identifier": {"id": "9", "scheme": "Bidders"},
                         "contactPoint": {"name": "A Person", "email": "person@example.com", "telephone": "+254700000000"}}]}


def award(amount, supplier):
    return {"id": f"a{amount}", "title": "Supply of health products", "value": {"amount": amount, "currency": "KES"},
            "suppliers": [{"id": "9", "name": supplier}]}


@pytest.fixture
def ocds_index(tmp_path, monkeypatch):
    path = tmp_path / "ocds.jsonl.gz"
    records = [release(REFERENCE, "SUPPLY OF HEALTH PRODUCTS (Liquid Dosage Forms)", "2024-11-13T00:00:00+03:00",
                       [award(1000000, "17.\tSynthetic Pharma Ltd"), award(0, "Zero Value Ltd"), award(900000000, "Outlier Ltd")]),
               release("ocds-5whusi-INVERTED", "Supply of liquid dosage medicines", "2024-01-01T00:00:00+03:00",
                       [award(2000000, "Other Pharma")], start="2024-02-01T00:00:00+03:00")]
    records += [release(f"ocds-5whusi-FILLER-{i}", "Office stationery", "2024-03-01T00:00:00+03:00",
                        [award(100000 + i, "Stationer")]) for i in range(150)]
    with gzip.open(path, "wt", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record) + "\n")
    target = tmp_path / "ocds.sqlite"
    build_index([{"path": path, "url": "https://example.invalid/test.jsonl.gz", "retrieved_at": "2026-10-15T00:00:00+00:00"}], target)
    monkeypatch.setenv("TENDER_OCDS_INDEX", str(target))
    return target


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
def service(tmp_path):
    return ProcurementService(Store(tmp_path / "cases"))


def in_process(service):
    async def call(store, tool, arguments):
        return getattr(service, tool)(**arguments)
    return call


async def borrowed_ok(store, case_id):
    case = store.get(case_id)
    return {"status": "SUCCESS", "tool": "filesystem.read_text_file",
            "manifest": {**case, "documents": [{k: v for k, v in d.items() if k != "extraction"} for d in case["documents"]]}}


async def borrowed_down(store, case_id):
    return {"status": "UNRESOLVED", "reason": "Borrowed Filesystem MCP is not installed; run npm ci"}


def test_ocds_index_flags_messy_records_and_drops_contacts(ocds_index):
    result = award_history(ocid=REFERENCE)
    awards = result["records"][0]["awards"]
    assert awards[0]["suppliers"][0]["normalized_name"] == "Synthetic Pharma Ltd"
    assert awards[0]["suppliers"][0]["published_name"] == "17.\tSynthetic Pharma Ltd"
    assert "SUPPLIER_NAME_HAS_LIST_NUMBER" in awards[0]["flags"] and not awards[0]["excluded_from_statistics"]
    assert awards[1]["flags"] == ["AWARD_VALUE_ZERO"] and awards[2]["flags"] == ["AWARD_VALUE_ABOVE_DATASET_P99"]
    assert result["summary"]["awards_used_for_statistics"] == 1 and result["summary"]["total_award_value"] == "1000000"
    citation = awards[2]["citation"]
    assert citation["pointer"] == "/awards/2" and citation["line"] == 1 and len(citation["file_sha256"]) == 64
    assert "unit-price" in result["price_note"]
    dump = "\n".join(sqlite3.connect(ocds_index).iterdump())
    assert "person@example.com" not in dump and "+254700000000" not in dump
    inverted = award_history(query="liquid dosage")["records"]
    assert any(f["flag"] == "TENDER_PERIOD_INVERTED" for r in inverted for f in r["flags"])


def test_award_history_reconciles_declared_closing_date(service, ocds_index):
    case = service.register_case(request())
    annex = service.search_award_history(case_id=case["id"])
    observation = annex["observations"][0]
    assert observation["type"] == "CLOSING_DATE_DISCREPANCY" and observation["status"] == "UNRESOLVED"
    assert (observation["declared_closed_on"], observation["published_closing_date"]) == ("2024-11-12", "2024-11-13")
    assert observation["citation"]["pointer"] == "/tender/tenderPeriod/endDate"
    plan = service.compile_evaluation_plan(case["id"])
    service.approve_plan(case["id"], dict(reviewer="TEST SIMULATION", digest=plan["digest"], confirmed=True))
    service.evaluate_bid_pack(case["id"], plan["id"])
    draft = service.draft_evaluation_file(case["id"])
    assert "public-award-history.json" in draft["files"]
    unresolved = json.loads(service.store.case_path(case["id"], f"drafts/{draft['id']}/unresolved-items.json").read_text(encoding="utf-8"))
    assert any(item.get("type") == "CLOSING_DATE_DISCREPANCY" for item in unresolved)


def test_missing_ocds_index_is_unresolved_not_an_error(service, tmp_path, monkeypatch):
    monkeypatch.setenv("TENDER_OCDS_INDEX", str(tmp_path / "absent.sqlite"))
    case = service.register_case(request())
    annex = service.search_award_history(case_id=case["id"])
    assert annex["result"]["status"] == "SOURCE_UNAVAILABLE"
    assert annex["observations"][0]["type"] == "SOURCE_UNAVAILABLE"


@pytest.mark.anyio
async def test_agent_plans_from_borrowed_manifest_and_pauses_for_human(service, ocds_index):
    case = service.register_case(request())
    workflow = Workflow(service.store, call=in_process(service), read_manifest=borrowed_ok)
    case = await workflow.advance(case["id"])
    assert case["state"] == "WAITING_FOR_PLAN_APPROVAL" and not case["plan"]["locked"]
    assert case["work_plan"]["steps"][:2] == ["compile_evaluation_plan", "search_award_history"]
    assert case["work_plan"]["manifest_source"] == "borrowed filesystem.read_text_file"
    assert case["award_history"]["observations"][0]["type"] == "CLOSING_DATE_DISCREPANCY"


@pytest.mark.anyio
async def test_agent_falls_back_when_borrowed_mcp_is_down(service, ocds_index):
    case = service.register_case(request())
    workflow = Workflow(service.store, call=in_process(service), read_manifest=borrowed_down)
    case = await workflow.advance(case["id"])
    assert case["work_plan"]["manifest_source"].startswith("local store")
    assert case["borrowed_mcp"]["status"] == "UNRESOLVED" and case["plan"]


def model_case(service):
    payload = request()
    payload["reference_ocid"] = None
    return service.register_case(payload)


def proposal(quote):
    return {"criteria": [{"id": "M01", "stage": "preliminary", "mandatory": True, "required_evidence": "Certificate",
                          "source": {"document_id": "doc_001", "page": 1, "section": "Criteria", "quote": quote}}]}


@pytest.mark.anyio
async def test_agent_retries_compile_with_validator_feedback(service, monkeypatch):
    case = model_case(service)
    seen = []
    def fake_model(documents, model, feedback=""):
        seen.append(feedback)
        quote = "A valid manufacturing certificate must be submitted." if feedback else "A paraphrased certificate rule."
        return proposal(quote), {"prompt_version": "test", "correction_feedback": feedback or None}
    monkeypatch.setattr("mcp_server.service.compile_with_model", fake_model)
    workflow = Workflow(service.store, call=in_process(service), read_manifest=borrowed_ok)
    case = await workflow.advance(case["id"], model="test-model")
    assert case["state"] == "WAITING_FOR_PLAN_APPROVAL"
    assert seen[0] == "" and "absent from the cited page" in seen[1]
    recovery = [e for e in service.store.events(case["id"]) if e["tool"] == "agent.recovery"]
    assert [e["status"] for e in recovery] == ["RETRY"]
    assert case["model_run"]["correction_feedback"] == seen[1]


@pytest.mark.anyio
async def test_agent_stops_for_human_after_retry_limit(service, monkeypatch):
    case = model_case(service)
    calls = []
    def always_invented(documents, model, feedback=""):
        calls.append(feedback)
        return proposal("An invented requirement."), {"prompt_version": "test"}
    monkeypatch.setattr("mcp_server.service.compile_with_model", always_invented)
    workflow = Workflow(service.store, call=in_process(service), read_manifest=borrowed_ok)
    case = await workflow.advance(case["id"], model="test-model")
    assert len(calls) == 3 and not case.get("plan")
    assert case["state"] == "HUMAN_RECOVERY_REQUIRED" and case["recovery"]["attempts"] == 3
    statuses = [e["status"] for e in service.store.events(case["id"]) if e["tool"] == "agent.recovery"]
    assert statuses == ["RETRY", "RETRY", "ESCALATED"]


@pytest.mark.anyio
async def test_native_tender_without_model_stops_after_one_attempt(service):
    payload = request()
    payload["reference_ocid"] = None
    payload["documents"][0]["name"] = "tender.txt"
    case = service.register_case(payload)
    workflow = Workflow(service.store, call=in_process(service), read_manifest=borrowed_ok)
    case = await workflow.advance(case["id"])
    assert case["state"] == "HUMAN_RECOVERY_REQUIRED" and case["recovery"]["attempts"] == 1
    assert "no local model" in case["work_plan"]["reasons"][0]


def test_positional_case_id_is_logged_against_the_case(service, ocds_index):
    # The MCP server once passed case_id positionally, which filed the event under the annex ID.
    case = service.register_case(request())
    service.search_award_history("", "", "", 10, case["id"])
    events = [e for e in service.store.events(case["id"]) if e["tool"] == "search_award_history"]
    assert [e["status"] for e in events] == ["STARTED", "SUCCESS"]
