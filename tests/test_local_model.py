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


def test_model_context_limit_before_runtime_call(monkeypatch):
    monkeypatch.delenv("TENDER_LOCAL_MODEL_URL", raising=False)
    monkeypatch.delenv("TENDER_LOCAL_MODEL_BACKEND", raising=False)
    documents = [{"id":"source", "sha256":"0"*64, "kind":"tender",
                  "extraction":{"pages":[{"page":1,"text":"x"*100_001}]}}]
    with pytest.raises(ValueError, match="bounded model context"):
        compile_with_model(documents, "candidate")
