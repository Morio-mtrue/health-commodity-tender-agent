from __future__ import annotations

import os
import hashlib
import json
import time
from copy import deepcopy
from typing import Literal
from pathlib import Path
from urllib.parse import urlparse
import httpx
from pydantic import BaseModel, ConfigDict, Field


class ModelSource(BaseModel):
    model_config=ConfigDict(extra="forbid")
    document_id: str
    page: int = Field(ge=1)
    section: str
    quote: str = Field(min_length=1)


class ModelCriterion(BaseModel):
    model_config=ConfigDict(extra="forbid")
    id: str
    stage: Literal["preliminary","technical","financial","due_diligence"]
    mandatory: bool
    required_evidence: str
    source: ModelSource
    supersedes: str | None


class ModelProposal(BaseModel):
    model_config=ConfigDict(extra="forbid")
    criteria: list[ModelCriterion] = Field(max_length=200)
    warnings: list[str] = Field(default_factory=list)


def extract_documents(client,url,backend,model,documents,prompt,schema):
    proposed={"criteria":[],"warnings":[]}
    requests=[]
    deadline=time.monotonic()+600
    for document in documents:
        if document["kind"]=="bid":
            continue
        pages=[{"document_id":document["id"],"kind":document["kind"],**page}
               for page in document["extraction"]["pages"]]
        if not any(page["text"].strip() for page in pages):
            raise ValueError("Source document has no readable native text; OCR or human source recovery is required")
        scoped=deepcopy(schema)
        scoped["$defs"]["ModelSource"]["properties"]["document_id"]["enum"]=[document["id"]]
        if document["kind"]=="tender":
            scoped["$defs"]["ModelCriterion"]["properties"]["supersedes"]={"type":"null"}
        system_prompt=prompt+"\nOutput JSON schema:\n"+json.dumps(scoped)
        messages=[{"role":"system","content":system_prompt},{"role":"user","content":json.dumps(pages)}]
        remaining=deadline-time.monotonic()
        if remaining<=0:
            raise ValueError("Total model extraction budget exceeded")
        if backend=="ollama":
            response=client.post(url+"/api/chat",json={"model":model,"stream":False,"format":scoped,
                "options":{"temperature":0,"num_ctx":16384,"num_gpu":0,"num_predict":5000},
                "messages":messages},timeout=httpx.Timeout(remaining,connect=5))
        else:
            response=client.post(url+"/v1/chat/completions",json={"model":model,"stream":False,
                "temperature":0,"max_tokens":5000,"response_format":{"type":"json_object"},
                "messages":messages},timeout=httpx.Timeout(remaining,connect=5))
        response.raise_for_status()
        raw=response.json()
        if backend=="ollama":
            if not raw.get("done") or raw.get("done_reason")=="length":
                raise ValueError("Model output was incomplete; criteria remain unapproved")
            output=json.loads(raw["message"]["content"])
        else:
            if raw["choices"][0].get("finish_reason")!="stop":
                raise ValueError("Model output was truncated; criteria remain unapproved")
            output=json.loads(raw["choices"][0]["message"]["content"])
        ModelProposal.model_validate(output)
        proposed["criteria"].extend(output["criteria"])
        proposed["warnings"].extend(output.get("warnings",[]))
        requests.append({"document_id":document["id"],"source_sha256":document["sha256"],
            "output_schema_sha256":hashlib.sha256(json.dumps(scoped,sort_keys=True).encode()).hexdigest(),
            "total_duration_ns":raw.get("total_duration"),"prompt_eval_count":raw.get("prompt_eval_count"),
            "eval_count":raw.get("eval_count"),"usage":raw.get("usage",{})})
    return proposed,{"document_requests":requests,
        "total_duration_ns":sum(r.get("total_duration_ns") or 0 for r in requests),
        "prompt_eval_count":sum(r.get("prompt_eval_count") or 0 for r in requests),
        "eval_count":sum(r.get("eval_count") or 0 for r in requests)}


def compile_with_model(documents, model):
    if model.lower().endswith((":cloud", "-cloud")):
        raise ValueError("Cloud models are not allowed in the local workbench")
    backend = os.getenv("TENDER_LOCAL_MODEL_BACKEND", "llamacpp" if model.endswith(".gguf") else "ollama")
    if backend not in {"ollama", "llamacpp"}:
        raise ValueError("Unsupported local model backend")
    default_url = "http://127.0.0.1:8081" if backend == "llamacpp" else "http://127.0.0.1:11434"
    url = os.getenv("TENDER_LOCAL_MODEL_URL", default_url).rstrip("/")
    parsed = urlparse(url)
    if parsed.scheme != "http" or parsed.hostname not in {"127.0.0.1", "localhost", "::1"} or parsed.username or parsed.password or parsed.path or parsed.query or parsed.fragment:
        raise ValueError("Model endpoint must be a local HTTP runtime without credentials")
    pages = [{"document_id": d["id"], "sha256": d["sha256"], **p}
             for d in documents if d["kind"] != "bid" for p in d["extraction"]["pages"]]
    size = sum(len(p["text"]) for p in pages)
    if size > 100_000:
        raise ValueError("Selected tender exceeds the bounded model context; choose cited excerpt pages")
    prompt = Path("prompts/criteria-v4.txt").read_text(encoding="utf-8")
    schema=ModelProposal.model_json_schema()
    prompt_digest=hashlib.sha256(prompt.encode()).hexdigest()
    schema_digest=hashlib.sha256(json.dumps(schema,sort_keys=True).encode()).hexdigest()
    # Small CPU models can need several minutes to emit a fully cited plan.
    with httpx.Client(timeout=httpx.Timeout(600, connect=5), trust_env=False) as client:
        if backend == "llamacpp":
            manifest = json.loads(Path(".runtime/model-manifest.json").read_text(encoding="utf-8"))
            if model != manifest["model_filename"]:
                raise ValueError("Selected model must match the pinned portable runtime manifest")
            served = client.get(url + "/v1/models")
            served.raise_for_status()
            identities = [str(item.get("id", "")).replace("\\", "/").split("/")[-1]
                          for item in served.json().get("data", [])]
            if model not in identities:
                raise ValueError("Local server is serving a different model than the pinned manifest")
            output,measurements=extract_documents(client,url,backend,model,documents,prompt,schema)
            return output, {**manifest,**measurements,"prompt_version":"criteria-v4","prompt_sha256":prompt_digest,
                            "output_schema_sha256":schema_digest}
        runtime = client.get(url + "/api/version")
        runtime.raise_for_status()
        tags = client.get(url + "/api/tags")
        tags.raise_for_status()
        selected = next((m for m in tags.json().get("models", []) if m.get("name") == model or m.get("model") == model), None)
        if not selected:
            raise ValueError("Model must be installed and selected by its exact runtime tag")
        if selected.get("remote_host") or selected.get("remote_model"):
            raise ValueError("Remote model aliases are not allowed in the local workbench")
        info = client.post(url + "/api/show", json={"model": model})
        info.raise_for_status()
        details=info.json()
        if details.get("remote_host") or details.get("remote_model") or details.get("details",{}).get("format") != "gguf":
            raise ValueError("Selected Ollama model must have verified local GGUF metadata")
        output,measurements=extract_documents(client,url,backend,model,documents,prompt,schema)
        return output, {**measurements,"runtime": "ollama", "runtime_version": runtime.json().get("version"),
                        "model": model, "model_digest": selected.get("digest"), "model_details": info.json().get("details"),
                        "prompt_version": "criteria-v4", "prompt_sha256":prompt_digest,
                        "output_schema_sha256":schema_digest}
