from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import urlparse
import httpx


def compile_with_model(documents, model):
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
    prompt = Path("prompts/criteria-v1.txt").read_text(encoding="utf-8")
    import json
    with httpx.Client(timeout=120, trust_env=False) as client:
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
            response = client.post(url + "/v1/chat/completions", json={"model":model,"stream":False,
                "temperature":0,"max_tokens":5000,"response_format":{"type":"json_object"},
                "messages":[{"role":"system","content":prompt},{"role":"user","content":json.dumps(pages)}]})
            response.raise_for_status()
            raw = response.json()
            if raw["choices"][0].get("finish_reason") != "stop":
                raise ValueError("Model output was truncated; criteria remain unapproved")
            output = json.loads(raw["choices"][0]["message"]["content"])
            return output, {**manifest,"prompt_version":"criteria-v1","usage":raw.get("usage",{})}
        runtime = client.get(url + "/api/version")
        runtime.raise_for_status()
        tags = client.get(url + "/api/tags")
        tags.raise_for_status()
        selected = next((m for m in tags.json().get("models", []) if m.get("name") == model or m.get("model") == model), None)
        if not selected:
            raise ValueError("Model must be installed and selected by its exact runtime tag")
        info = client.post(url + "/api/show", json={"model": model})
        info.raise_for_status()
        response = client.post(url + "/api/chat", json={"model": model, "stream": False, "format": "json",
            "options": {"temperature": 0, "num_ctx": 16384}, "messages": [
                {"role": "system", "content": prompt},
                {"role": "user", "content": json.dumps(pages)}]})
        response.raise_for_status()
        raw = response.json()
        output = json.loads(raw["message"]["content"])
        return output, {"runtime": "ollama", "runtime_version": runtime.json().get("version"),
                        "model": model, "model_digest": selected.get("digest"), "model_details": info.json().get("details"),
                        "prompt_version": "criteria-v1", "total_duration_ns": raw.get("total_duration"),
                        "prompt_eval_count": raw.get("prompt_eval_count"), "eval_count": raw.get("eval_count")}
