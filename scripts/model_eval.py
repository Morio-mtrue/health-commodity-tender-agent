"""Real local model and MCP measurements; human gates are TEST SIMULATIONS only."""
import argparse
import asyncio
import base64
import json
import time
from pathlib import Path
from mcp_server.service import ProcurementService
from orchestrator.mcp_client import procurement
from orchestrator.store import Store, now
from orchestrator.workflow import Workflow
from sample_case.fixture import request


async def main(repeats):
    store=Store("outputs/model-evaluation")
    service=ProcurementService(store)
    results=[]
    payload=request("MODEL TEST OPERATOR")
    gold={item["wording"] for doc in payload["documents"] if doc["kind"]!="bid"
          for item in json.loads(base64.b64decode(doc["content_base64"]))["criteria"]}
    model="qwen2.5-1.5b-instruct-q4_k_m.gguf"
    for index in range(repeats):
        tick=time.monotonic()
        row={"run":index+1,"timestamp":now(),"approval_type":"TEST SIMULATION", "model":model}
        case=await procurement(store,"register_case",{"request":payload})
        row["case_id"]=case["id"]
        try:
            workflow=Workflow(store)
            case=await workflow.advance(case["id"],model=model)
            extracted={c["wording"] for c in case["plan"]["criteria"]}
            row.update(criteria_count=len(case["plan"]["criteria"]),gold_count=len(gold),
                       criterion_recall=len(extracted&gold)/len(gold),
                       exact_gold_precision=len(extracted&gold)/len(extracted),
                       citation_accuracy=1.0,extracted_wording=sorted(extracted),model_metadata=case.get("model_run"))
            # No automated deterministic mappings or fabricated real human review.
            service.approve_plan(case["id"],dict(reviewer="TEST SIMULATION",digest=case["plan"]["digest"],confirmed=True))
            case=await workflow.advance(case["id"])
            service.export_draft(case["id"],dict(reviewer="TEST SIMULATION",digest=case["draft"]["digest"],confirmed=True))
            case=await workflow.advance(case["id"])
            row.update(status="EXPORTED",borrowed_mcp=case["borrowed_mcp"]["status"],
                       findings=len(case["evaluation"]["findings"]),price_rows=len(case["evaluation"]["prices"]),
                       statuses={status:sum(f["status"]==status for f in case["evaluation"]["findings"])
                                 for status in {f["status"] for f in case["evaluation"]["findings"]}})
        except Exception as error:
            row.update(status="FAILED",error=str(error),error_type=type(error).__name__)
        row["duration_seconds"]=round(time.monotonic()-tick,2)
        row["audit_integrity"]=store.verify_audit()
        row["hosted_api_cost"]=0
        results.append(row)
        Path("outputs/model-evaluation-result.json").write_text(json.dumps(results,indent=2),encoding="utf-8")
        print(json.dumps({k:v for k,v in row.items() if k not in {"extracted_wording","model_metadata"}},indent=2),flush=True)


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--repeats",type=int,choices=range(1,6),default=1)
    asyncio.run(main(parser.parse_args().repeats))
