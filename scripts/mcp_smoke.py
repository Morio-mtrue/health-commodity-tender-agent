"""Actual MCP integration run. All reviewer approvals here are TEST SIMULATIONS."""
import asyncio
import json
import time
from pathlib import Path
from mcp_server.service import ProcurementService
from orchestrator.mcp_client import procurement
from orchestrator.store import Store, now
from orchestrator.workflow import Workflow
from sample_case.fixture import request


async def main():
    started=time.monotonic()
    store=Store("outputs/mcp-integration")
    workflow=Workflow(store)
    service=ProcurementService(store)
    case=await procurement(store,"register_case",{"request":request("INTEGRATION TEST OPERATOR")})
    case=await workflow.advance(case["id"])
    assert case["state"]=="WAITING_FOR_PLAN_APPROVAL" and not case["plan"]["locked"]
    assert case["borrowed_mcp"]["status"]=="SUCCESS",case["borrowed_mcp"]
    assert "search_award_history" in case["work_plan"]["steps"]
    service.approve_plan(case["id"],dict(reviewer="TEST SIMULATION",digest=case["plan"]["digest"],confirmed=True))
    case=await workflow.advance(case["id"])
    assert case["state"]=="WAITING_FOR_EXPORT_APPROVAL"
    service.export_draft(case["id"],dict(reviewer="TEST SIMULATION",digest=case["draft"]["digest"],confirmed=True))
    case=await workflow.advance(case["id"])
    assert case["state"]=="EXPORTED"
    result={"timestamp":now(),"case_id":case["id"],"duration_seconds":round(time.monotonic()-started,2),
            "custom_mcp_tools":5,"borrowed_mcp":{k:v for k,v in case["borrowed_mcp"].items() if k!="manifest"},
            "work_plan":case["work_plan"],
            "award_history":{"status":case["award_history"]["result"]["status"],
                             "summary":case["award_history"]["result"].get("summary"),
                             "observations":case["award_history"]["observations"]},
            "findings":len(case["evaluation"]["findings"]),
            "price_rows":len(case["evaluation"]["prices"]),"audit_integrity":store.verify_audit(),
            "approval_type":"TEST SIMULATION - not a human committee approval","model_run":False,
            "versions":service.runtime_versions()}
    Path("outputs/mcp-integration-result.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
    print(json.dumps(result,indent=2))


if __name__=="__main__":
    asyncio.run(main())
