"""Compile a fresh real local-model case; leave every approval to the human UI."""
import argparse
import asyncio
import json
from pathlib import Path
from orchestrator.mcp_client import procurement
from orchestrator.store import Store
from orchestrator.workflow import Workflow
from scripts.model_eval import native_tender_payload


async def main(model):
    store=Store("outputs")
    payload=native_tender_payload("Demo operator")
    payload["name"]="Open-weights · synthetic review"
    case=await procurement(store,"register_case",{"request":payload})
    case=await Workflow(store).advance(case["id"],model=model)
    result={"case_id":case["id"],"state":case["state"],"criteria_count":len(case["plan"]["criteria"]),
            "model_run":case["model_run"],"approvals":case["approvals"],"audit_integrity":store.verify_audit()}
    Path("outputs/model-human-review-result.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
    print(json.dumps(result,indent=2))


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--model",default="tender-qwen:1.5b-q4")
    asyncio.run(main(parser.parse_args().model))
