from __future__ import annotations

import asyncio
import json
import secrets
from pathlib import Path
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from pydantic import BaseModel, Field
from mcp_server.service import ProcurementService
from mcp_server.schemas.models import ApprovalRequest
from orchestrator.mcp_client import procurement
from orchestrator.store import Store
from orchestrator.workflow import Workflow
from sample_case.fixture import request as demo_request


class AdvanceRequest(BaseModel):
    model: str = Field(default="", max_length=150)
    live_sources: bool = False


def create_app(root=None):
    app = FastAPI(title="Health Tender Workbench", docs_url=None, redoc_url=None)
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["localhost","127.0.0.1","[::1]","testserver"])
    store = Store(root)
    service, workflow, token = ProcurementService(store), Workflow(store), secrets.token_urlsafe(32)
    app.state.store, app.state.service = store, service
    action_lock = asyncio.Lock()

    @app.middleware("http")
    async def headers(request, call_next):
        response = await call_next(request)
        response.headers.update({"X-Content-Type-Options":"nosniff", "Referrer-Policy":"no-referrer", "Cache-Control":"no-store"})
        if "Content-Security-Policy" not in response.headers:
            response.headers["Content-Security-Policy"]="default-src 'self'; style-src 'self'; script-src 'self'; img-src 'self' data:; frame-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'self'"
        return response

    async def human_ui(request: Request):
        if request.headers.get("X-Workbench-Token") != token:
            raise HTTPException(403,"Local review session token is required")
        origin = request.headers.get("origin")
        if origin and origin not in {"http://localhost:8000","http://127.0.0.1:8000"}:
            raise HTTPException(403,"Cross-origin actions are not allowed")

    @app.exception_handler(ValueError)
    async def bad_input(request, error):
        return JSONResponse(status_code=400, content={"detail":str(error)})

    @app.get("/api/session")
    def session():
        return {"token":token, "model_runtime":"Ollama (local)", "model_required_for_pdf_criteria":True}

    @app.get("/api/cases")
    def cases():
        return [{"id":c["id"],"name":c["name"],"state":c["state"],"created_at":c["created_at"]} for c in store.list()]

    @app.get("/api/cases/{case_id}")
    def case(case_id: str):
        return store.get(case_id)

    @app.post("/api/demo", dependencies=[Depends(human_ui)])
    async def demo():
        async with action_lock:
            return await procurement(store,"register_case",{"request":demo_request()})

    @app.post("/api/cases", dependencies=[Depends(human_ui)])
    async def register(request: Request):
        if int(request.headers.get("content-length",0)) > 100_000_000:
            raise HTTPException(413,"Case upload exceeds limit")
        raw = await request.body()
        if len(raw)>100_000_000:
            raise HTTPException(413,"Case upload exceeds limit")
        async with action_lock:
            return await procurement(store,"register_case",{"request":json.loads(raw)})

    @app.post("/api/cases/{case_id}/advance", dependencies=[Depends(human_ui)])
    async def advance(case_id: str, settings: AdvanceRequest):
        async with action_lock:
            return await workflow.advance(case_id, settings.model, settings.live_sources)

    @app.post("/api/cases/{case_id}/plan/approve", dependencies=[Depends(human_ui)])
    async def approve(case_id: str, approval: ApprovalRequest):
        async with action_lock:
            return service.approve_plan(case_id, approval.model_dump())

    @app.post("/api/cases/{case_id}/plan/revise", dependencies=[Depends(human_ui)])
    async def revise(case_id: str, request: Request):
        async with action_lock:
            payload = await request.json()
            return service.revise_plan(case_id,payload["criteria"])

    @app.post("/api/cases/{case_id}/export", dependencies=[Depends(human_ui)])
    async def export(case_id: str, approval: ApprovalRequest):
        async with action_lock:
            return service.export_draft(case_id, approval.model_dump())

    @app.get("/api/cases/{case_id}/audit")
    def audit(case_id: str):
        store.get(case_id)
        return {"integrity_valid":store.verify_audit(),"events":store.events(case_id)}

    @app.get("/api/cases/{case_id}/documents/{document_id}")
    def document(case_id: str, document_id: str):
        data=store.get(case_id)
        doc=next((d for d in data["documents"] if d["id"]==document_id),None)
        if not doc:
            raise HTTPException(404,"Document not found")
        # Text is escaped by the UI; PDF downloads are attachments, never embedded executables.
        return {"id":doc["id"],"name":doc["name"],"sha256":doc["sha256"],"pages":doc["extraction"]["pages"]}

    @app.get("/api/cases/{case_id}/report")
    def report(case_id: str):
        case=store.get(case_id)
        if not case.get("draft"):
            raise HTTPException(404,"Draft is not ready")
        path=store.case_path(case_id,f"drafts/{case['draft']['id']}/report.html")
        response=Response(path.read_text(encoding="utf-8"),media_type="text/html")
        response.headers["Content-Security-Policy"]="sandbox; default-src 'none'; style-src 'unsafe-inline'"
        return response

    @app.get("/api/cases/{case_id}/download")
    def download(case_id: str):
        case=store.get(case_id)
        if not case.get("draft",{}).get("exported") or case["state"]!="EXPORTED":
            raise HTTPException(403,"Named export approval is required")
        return FileResponse(store.case_path(case_id,case["draft"]["export_path"]),filename="unsigned-evaluation-package.zip",media_type="application/zip")

    @app.get("/")
    def index():
        return FileResponse(Path("app/static/index.html"))

    app.mount("/static", StaticFiles(directory="app/static"),name="static")
    return app


app = create_app()
