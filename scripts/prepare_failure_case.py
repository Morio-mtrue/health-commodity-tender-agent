"""Create a case where the agent must stop for a human: a native-text tender with no local model.

uv run python -m scripts.prepare_failure_case
The case appears in the workbench case picker in state HUMAN_RECOVERY_REQUIRED. No approval is simulated.
"""
import asyncio

from orchestrator.mcp_client import procurement
from orchestrator.store import Store
from orchestrator.workflow import Workflow
from scripts.model_eval import native_tender_payload


async def main():
    store = Store()
    payload = native_tender_payload("Demo operator")
    payload.update(name="Native tender, no model selected (expected stop)", reference_ocid=None)
    case = await procurement(store, "register_case", {"request": payload})
    case = await Workflow(store).advance(case["id"])
    print(case["id"], case["state"], "-", case["recovery"]["reason"])


if __name__ == "__main__":
    asyncio.run(main())
