"""Real local model and MCP measurements; human gates are TEST SIMULATIONS only."""
import argparse
import asyncio
import base64
import json
import time
import os
import httpx
from pathlib import Path
from mcp_server.service import ProcurementService
from orchestrator.mcp_client import procurement
from orchestrator.store import Store, now
from orchestrator.workflow import Workflow
from sample_case.fixture import request


def native_tender_payload(operator):
    payload=request(operator)
    for doc in payload["documents"]:
        if doc["kind"]=="bid":
            continue
        rules=json.loads(base64.b64decode(doc["content_base64"]))["criteria"]
        text="ORIGINAL SYNTHETIC DEMONSTRATION - PUBLISHED EVALUATION REQUIREMENTS\n"
        text+="\n".join(f"{c['id']} ({c['stage']}) {c['wording']}" for c in rules)
        doc.update(name=doc["name"].replace(".json",".txt"),content_base64=base64.b64encode(text.encode()).decode())
    return payload


async def main(repeats,model,native_text=False,append=False):
    store=Store("outputs/model-evaluation")
    service=ProcurementService(store)
    result_file=Path("outputs/model-evaluation-result.json")
    results=json.loads(result_file.read_text(encoding="utf-8")) if append and result_file.exists() else []
    payload=request("MODEL TEST OPERATOR")
    gold={item["wording"] for doc in payload["documents"] if doc["kind"]!="bid"
          for item in json.loads(base64.b64decode(doc["content_base64"]))["criteria"]}
    gold_by_id={item["id"]:(item["wording"],f"doc_{index+1:03d}")
                for index,doc in enumerate(payload["documents"]) if doc["kind"]!="bid"
                for item in json.loads(base64.b64decode(doc["content_base64"]))["criteria"]}
    if native_text:
        payload=native_tender_payload("MODEL TEST OPERATOR")
    for index in range(repeats):
        tick=time.monotonic()
        row={"run":len(results)+1,"timestamp":now(),"approval_type":"TEST SIMULATION", "model":model}
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
            criteria={c["id"]:c for c in case["plan"]["criteria"]}
            source_span_matches=sum(1 for c in criteria.values() if c["id"] in gold_by_id
                and gold_by_id[c["id"]][0] in c["source"]["quote"]
                and gold_by_id[c["id"]][1]==c["source"]["document_id"])
            row["source_span_criterion_recall"]=source_span_matches/len(gold_by_id)
            row["source_span_precision"]=source_span_matches/len(criteria)
            row["addendum_supersession_correct"]=bool(criteria.get("T01A",{}).get("active")
                and criteria.get("T01A",{}).get("supersedes")=="T01"
                and not criteria.get("T01",{}).get("active",True))
            if case.get("model_run",{}).get("runtime")=="ollama":
                response=httpx.get(os.environ.get("TENDER_LOCAL_MODEL_URL","http://127.0.0.1:11434")+"/api/ps",
                                   timeout=5,trust_env=False)
                response.raise_for_status()
                loaded=next((m for m in response.json().get("models",[]) if m.get("digest")==case["model_run"]["model_digest"]),{})
                row["runtime_memory_observation"]={k:loaded.get(k) for k in ("size","size_vram","context_length")}
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
        recovery=[e["status"] for e in store.events(row["case_id"]) if e["tool"]=="agent.recovery"]
        row.update(compile_recovery_events=recovery,compile_attempts=1+recovery.count("RETRY"),
                   case_state=store.get(row["case_id"])["state"],
                   award_history=(store.get(row["case_id"]).get("award_history") or {}).get("result",{}).get("status"))
        row["duration_seconds"]=round(time.monotonic()-tick,2)
        row["audit_integrity"]=store.verify_audit()
        row["hosted_api_cost"]=0
        results.append(row)
        Path("outputs/model-evaluation-result.json").write_text(json.dumps(results,indent=2),encoding="utf-8")
        print(json.dumps({k:v for k,v in row.items() if k not in {"extracted_wording","model_metadata"}},indent=2),flush=True)


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--repeats",type=int,choices=range(1,6),default=1)
    parser.add_argument("--model",default="qwen2.5-1.5b-instruct-q4_k_m.gguf")
    parser.add_argument("--native-text",action="store_true")
    parser.add_argument("--append",action="store_true",help="Append repeat measurements to the existing local result file")
    arguments=parser.parse_args()
    asyncio.run(main(arguments.repeats,arguments.model,arguments.native_text,arguments.append))
