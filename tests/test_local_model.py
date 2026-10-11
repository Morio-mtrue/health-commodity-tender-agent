import pytest
from connectors.local_model import compile_with_model


@pytest.mark.parametrize("url", ["https://127.0.0.1", "http://example.org", "http://127.0.0.1@example.org",
                                    "http://user:secret@localhost", "http://127.0.0.1/api", "http://localhost?target=remote"])
def test_nonlocal_or_credential_model_endpoint_rejected(monkeypatch, url):
    monkeypatch.setenv("TENDER_LOCAL_MODEL_URL", url)
    with pytest.raises(ValueError, match="local HTTP"):
        compile_with_model([], "candidate")


def test_unknown_backend_rejected(monkeypatch):
    monkeypatch.setenv("TENDER_LOCAL_MODEL_BACKEND", "hosted")
    with pytest.raises(ValueError, match="Unsupported"):
        compile_with_model([], "candidate")


@pytest.mark.parametrize("model", ["gemma4:cloud", "alias:7b-cloud"])
def test_cloud_model_selector_rejected_before_any_http_call(model):
    with pytest.raises(ValueError,match="Cloud models"):
        compile_with_model([],model)


def test_remote_alias_rejected_before_prompts_are_sent(monkeypatch):
    import httpx
    import connectors.local_model as adapter
    calls=[]
    def handler(request):
        calls.append(request.url.path)
        if request.url.path=="/api/version":
            return httpx.Response(200,json={"version":"test"})
        if request.url.path=="/api/tags":
            return httpx.Response(200,json={"models":[{"name":"apparently-local","remote_host":"https://remote.example.org"}]})
        raise AssertionError("No prompt or show request may be sent for a remote alias")
    original_client=httpx.Client
    monkeypatch.setattr(adapter.httpx,"Client",lambda **kw:original_client(transport=httpx.MockTransport(handler),**kw))
    monkeypatch.delenv("TENDER_LOCAL_MODEL_URL",raising=False)
    monkeypatch.delenv("TENDER_LOCAL_MODEL_BACKEND",raising=False)
    with pytest.raises(ValueError,match="Remote model aliases"):
        compile_with_model([],"apparently-local")
    assert calls==["/api/version","/api/tags"]


def test_model_context_limit_before_runtime_call(monkeypatch):
    monkeypatch.delenv("TENDER_LOCAL_MODEL_URL", raising=False)
    monkeypatch.delenv("TENDER_LOCAL_MODEL_BACKEND", raising=False)
    documents = [{"id":"source", "sha256":"0"*64, "kind":"tender",
                  "extraction":{"pages":[{"page":1,"text":"x"*100_001}]}}]
    with pytest.raises(ValueError, match="bounded model context"):
        compile_with_model(documents, "candidate")


@pytest.mark.parametrize("truncated",[False,True])
def test_document_scoping_excludes_bids_and_rejects_incomplete_output(monkeypatch,truncated):
    import json
    import httpx
    import connectors.local_model as adapter
    sent=[]
    def handler(request):
        if request.url.path=="/api/version":
            return httpx.Response(200,json={"version":"test"})
        if request.url.path=="/api/tags":
            return httpx.Response(200,json={"models":[{"name":"local","digest":"test"}]})
        if request.url.path=="/api/show":
            return httpx.Response(200,json={"details":{"format":"gguf"}})
        body=json.loads(request.content)
        pages=json.loads(body["messages"][1]["content"])
        assert len(pages)==1 and "private bid" not in pages[0]["text"]
        source=pages[0]
        sent.append(source["document_id"])
        item={"id":"C"+str(len(sent)),"stage":"technical","mandatory":True,
              "required_evidence":"Human review","supersedes":None,
              "source":{"document_id":source["document_id"],"page":1,"section":"","quote":source["text"]}}
        return httpx.Response(200,json={"done":True,"done_reason":"length" if truncated else "stop",
                                      "message":{"content":json.dumps({"criteria":[item]})}})
    original_client=httpx.Client
    monkeypatch.setattr(adapter.httpx,"Client",lambda **kw:original_client(transport=httpx.MockTransport(handler),**kw))
    monkeypatch.delenv("TENDER_LOCAL_MODEL_URL",raising=False)
    monkeypatch.setenv("TENDER_LOCAL_MODEL_BACKEND","ollama")
    documents=[{"id":name,"sha256":"0"*64,"kind":kind,
                "extraction":{"pages":[{"page":1,"text":content}]}}
               for name,kind,content in [("doc_001","tender","Original requirement."),
                  ("doc_002","addendum","Amended requirement."),("doc_003","bid","private bid data")]]
    if truncated:
        with pytest.raises(ValueError,match="incomplete"):
            compile_with_model(documents,"local")
        assert sent==["doc_001"]
    else:
        proposal,metadata=compile_with_model(documents,"local")
        assert sent==["doc_001","doc_002"]
        assert len(proposal["criteria"])==2 and len(metadata["document_requests"])==2
