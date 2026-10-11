from __future__ import annotations

from typing import TypedDict
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt
from orchestrator.mcp_client import borrowed_manifest_read, procurement


class WorkflowState(TypedDict, total=False):
    case_id: str
    model: str
    live_sources: bool
    borrowed: dict
    plan_id: str
    draft_id: str


class Workflow:
    """Graph checkpoints are in memory; case DB is authoritative across restarts."""

    def __init__(self, store):
        self.store = store
        graph = StateGraph(WorkflowState)
        graph.add_node("compile", self.compile)
        graph.add_node("plan_gate", self.plan_gate)
        graph.add_node("borrowed", self.borrowed)
        graph.add_node("evaluate", self.evaluate)
        graph.add_node("draft", self.draft)
        graph.add_node("export_gate", self.export_gate)
        graph.add_conditional_edges(START, self.route)
        graph.add_edge("compile", "plan_gate")
        graph.add_edge("plan_gate", "borrowed")
        graph.add_edge("borrowed", "evaluate")
        graph.add_edge("evaluate", "draft")
        graph.add_edge("draft", "export_gate")
        graph.add_edge("export_gate", END)
        self.graph = graph.compile(checkpointer=InMemorySaver())

    def route(self, state):
        case = self.store.get(state["case_id"])
        if case.get("draft"):
            return "export_gate"
        return "plan_gate" if case.get("plan") else "compile"

    async def compile(self, state):
        plan = await procurement(self.store, "compile_evaluation_plan", {"case_id": state["case_id"], "model": state.get("model", "")})
        return {"plan_id": plan["id"]}

    def plan_gate(self, state):
        case = self.store.get(state["case_id"])
        if not case["plan"]["locked"]:
            interrupt({"gate": "named_plan_approval", "digest": case["plan"]["digest"]})
            case = self.store.get(state["case_id"])
        if not case["plan"]["locked"]:
            raise ValueError("Human plan approval has not been recorded")
        return {"plan_id": case["plan"]["id"]}

    async def borrowed(self, state):
        result = await borrowed_manifest_read(self.store, state["case_id"])
        case = self.store.get(state["case_id"])
        case["borrowed_mcp"] = result
        self.store.save(case)
        return {"borrowed": result}

    async def evaluate(self, state):
        await procurement(self.store, "evaluate_bid_pack", {"case_id": state["case_id"],
            "locked_plan_id": state["plan_id"], "live_sources": state.get("live_sources", False)})
        return {}

    async def draft(self, state):
        draft = await procurement(self.store, "draft_evaluation_file", {"case_id": state["case_id"]})
        return {"draft_id": draft["id"]}

    def export_gate(self, state):
        case = self.store.get(state["case_id"])
        if not case["draft"]["exported"]:
            interrupt({"gate": "named_export_approval", "digest": case["draft"]["digest"]})
            case = self.store.get(state["case_id"])
        if not case["draft"]["exported"]:
            raise ValueError("Human export approval has not been recorded")
        return {}

    async def advance(self, case_id, model="", live_sources=False):
        case = self.store.get(case_id)
        # Use revision-specific thread IDs so human edits never replay a stale checkpoint.
        revision = case.get("plan", {}).get("revision", 0)
        config = {"configurable": {"thread_id": f"{case_id}:revision:{revision}"}}
        snapshot = self.graph.get_state(config)
        data = Command(resume=True) if snapshot.next else {"case_id":case_id, "model":model, "live_sources":live_sources}
        await self.graph.ainvoke(data, config=config)
        return self.store.get(case_id)
