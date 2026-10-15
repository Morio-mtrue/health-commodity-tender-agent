from __future__ import annotations

from typing import TypedDict
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt
from orchestrator.mcp_client import borrowed_manifest_read, procurement

MODEL_COMPILE_ATTEMPTS = 3


class WorkflowState(TypedDict, total=False):
    case_id: str
    model: str
    live_sources: bool
    work_plan: list[str]
    attempt_limit: int
    attempts: int
    feedback: str
    compile_error: str
    plan_id: str
    draft_id: str


def plan_work(manifest, model):
    """Choose the steps for this case from its manifest. Deterministic on purpose: a 1.5B local model
    is not trusted to pick tools, and every choice is written to the audit log with its reason."""
    rule_documents = [d for d in manifest["documents"] if d["kind"] != "bid"]
    native = [d["name"] for d in rule_documents if not d["name"].lower().endswith(".json")]
    steps, reasons = ["compile_evaluation_plan"], []
    if native and not model:
        reasons.append(f"{len(native)} tender document(s) need model extraction but no local model is selected; "
                       "compilation will stop for human source recovery.")
    elif model:
        reasons.append(f"Criteria come from local model {model}; up to {MODEL_COMPILE_ATTEMPTS} attempts, "
                       "each retry receives the validator's rejection.")
    else:
        reasons.append("Structured synthetic criteria; no model call needed.")
    if manifest.get("reference_ocid"):
        steps.append("search_award_history")
        reasons.append(f"Reference {manifest['reference_ocid']} is linked: fetch its published award history and "
                       "compare closing dates before the plan is locked.")
    steps += ["named_plan_approval", "evaluate_bid_pack", "draft_evaluation_file", "named_export_approval"]
    recovery = [w for w in manifest.get("warnings", []) if "OCR_FAILED" in w or "MISSING_DOCUMENT" in w]
    if recovery:
        reasons.append(f"{len(recovery)} extraction warning(s) will stay UNRESOLVED for human review.")
    return {"steps": steps, "reasons": reasons, "compile_attempt_limit": MODEL_COMPILE_ATTEMPTS if model else 1,
            "documents_needing_recovery": recovery}


class Workflow:
    """Graph checkpoints are in memory; case DB is authoritative across restarts.
    call and read_manifest are injectable so tests can run the graph without subprocesses."""

    def __init__(self, store, call=procurement, read_manifest=borrowed_manifest_read):
        self.store, self.call, self.read_manifest = store, call, read_manifest
        graph = StateGraph(WorkflowState)
        graph.add_node("inspect", self.inspect)
        graph.add_node("compile", self.compile)
        graph.add_node("needs_human", self.needs_human)
        graph.add_node("award_history", self.award_history)
        graph.add_node("plan_gate", self.plan_gate)
        graph.add_node("evaluate", self.evaluate)
        graph.add_node("draft", self.draft)
        graph.add_node("export_gate", self.export_gate)
        graph.add_conditional_edges(START, self.route)
        graph.add_edge("inspect", "compile")
        graph.add_conditional_edges("compile", self.after_compile)
        graph.add_edge("needs_human", END)
        graph.add_edge("award_history", "plan_gate")
        graph.add_edge("plan_gate", "evaluate")
        graph.add_edge("evaluate", "draft")
        graph.add_edge("draft", "export_gate")
        graph.add_edge("export_gate", END)
        self.graph = graph.compile(checkpointer=InMemorySaver())

    def route(self, state):
        case = self.store.get(state["case_id"])
        if case.get("draft"):
            return "export_gate"
        return "plan_gate" if case.get("plan") else "inspect"

    async def inspect(self, state):
        case_id = state["case_id"]
        borrowed = await self.read_manifest(self.store, case_id)
        manifest = borrowed.pop("manifest", None)
        source = "borrowed filesystem.read_text_file"
        if manifest is None:
            # Recovery: plan from the local store when the borrowed server is unavailable.
            case = self.store.get(case_id)
            manifest = {**case, "documents": [{k: v for k, v in d.items() if k != "extraction"} for d in case["documents"]]}
            source = "local store (borrowed MCP unavailable)"
        work = plan_work(manifest, state.get("model", ""))
        case = self.store.get(case_id)
        case.update(borrowed_mcp=borrowed, work_plan={**work, "manifest_source": source}, recovery=None)
        self.store.save(case)
        self.store.event("agent.work_plan", case_id, {"manifest_source": source, "model": state.get("model", "")}, work, "SUCCESS")
        return {"work_plan": work["steps"], "attempt_limit": work["compile_attempt_limit"]}

    async def compile(self, state):
        attempt = state.get("attempts", 0) + 1
        arguments = {"case_id": state["case_id"], "model": state.get("model", "")}
        if state.get("feedback"):
            arguments["feedback"] = state["feedback"]
        try:
            plan = await self.call(self.store, "compile_evaluation_plan", arguments)
        except ValueError as error:
            retry = attempt < state.get("attempt_limit", 1)
            self.store.event("agent.recovery", state["case_id"], {"step": "compile_evaluation_plan", "attempt": attempt},
                             {"error": str(error), "next": "retry with validator feedback" if retry else "stop for human"},
                             "RETRY" if retry else "ESCALATED")
            return {"attempts": attempt, "compile_error": str(error), "feedback": str(error)[:2000]}
        return {"attempts": attempt, "compile_error": "", "feedback": "", "plan_id": plan["id"]}

    def after_compile(self, state):
        if not state.get("compile_error"):
            return "award_history" if "search_award_history" in state.get("work_plan", []) else "plan_gate"
        return "compile" if state["attempts"] < state.get("attempt_limit", 1) else "needs_human"

    def needs_human(self, state):
        case = self.store.get(state["case_id"])
        case.update(state="HUMAN_RECOVERY_REQUIRED",
                    recovery={"step": "compile_evaluation_plan", "attempts": state["attempts"], "reason": state["compile_error"],
                              "action": "Correct the source documents or model choice, then compile again. No criteria were invented."})
        self.store.save(case)
        return {}

    async def award_history(self, state):
        try:
            await self.call(self.store, "search_award_history", {"case_id": state["case_id"]})
        except ValueError as error:
            # Public context is optional: record the failure and continue to the human gate.
            self.store.event("agent.recovery", state["case_id"], {"step": "search_award_history"},
                             {"error": str(error), "next": "continue without public award history"}, "SKIPPED")
        return {}

    def plan_gate(self, state):
        case = self.store.get(state["case_id"])
        if not case["plan"]["locked"]:
            interrupt({"gate": "named_plan_approval", "digest": case["plan"]["digest"]})
            case = self.store.get(state["case_id"])
        if not case["plan"]["locked"]:
            raise ValueError("Human plan approval has not been recorded")
        return {"plan_id": case["plan"]["id"]}

    async def evaluate(self, state):
        await self.call(self.store, "evaluate_bid_pack", {"case_id": state["case_id"],
            "locked_plan_id": state["plan_id"], "live_sources": state.get("live_sources", False)})
        return {}

    async def draft(self, state):
        draft = await self.call(self.store, "draft_evaluation_file", {"case_id": state["case_id"]})
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
        data = Command(resume=True) if snapshot.next else {"case_id": case_id, "model": model, "live_sources": live_sources,
                                                           "attempts": 0, "feedback": "", "compile_error": ""}
        await self.graph.ainvoke(data, config=config)
        return self.store.get(case_id)
