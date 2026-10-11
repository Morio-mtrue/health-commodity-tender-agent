import hashlib
import httpx
import pytest
from scripts.setup_cpu_model import download


def test_resume_checks_range_and_final_checksum(tmp_path):
    target=tmp_path/"model.gguf"
    target.with_suffix(".gguf.part").write_bytes(b"first")
    def handler(request):
        assert request.headers["range"]=="bytes=5-"
        return httpx.Response(206,headers={"content-range":"bytes 5-8/9"},content=b"last")
    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        checksum=download(client,"https://example.org/model",target,hashlib.sha256(b"firstlast").hexdigest())
    assert target.read_bytes()==b"firstlast" and checksum==hashlib.sha256(b"firstlast").hexdigest()


def test_bad_range_or_checksum_never_promotes_partial_file(tmp_path):
    target=tmp_path/"model.gguf"
    target.with_suffix(".gguf.part").write_bytes(b"first")
    with httpx.Client(transport=httpx.MockTransport(lambda r:httpx.Response(206,headers={"content-range":"bytes 0-3/4"},content=b"last"))) as client:
        with pytest.raises(ValueError,match="different download range"):
            download(client,"https://example.org/model",target,"0"*64)
    assert not target.exists()
    with httpx.Client(transport=httpx.MockTransport(lambda r:httpx.Response(200,content=b"wrong"))) as client:
        with pytest.raises(ValueError,match="checksum mismatch"):
            download(client,"https://example.org/model",target,"0"*64)
    assert not target.exists()
