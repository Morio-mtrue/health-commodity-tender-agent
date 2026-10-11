"""Fetch an official release installer for Windows signature verification before use."""
import json
from pathlib import Path
import httpx
from scripts.setup_cpu_model import download


if __name__=="__main__":
    with httpx.Client(timeout=60,follow_redirects=True) as client:
        source="https://ollama.com/download/OllamaSetup.exe"
        target=Path(".runtime/OllamaSetup.exe")
        target.parent.mkdir(exist_ok=True)
        # Official download uses TLS; Windows Authenticode must establish the publisher
        # before execution. The recorded SHA is provenance, not a publisher checksum.
        checksum=download(client,source,target,max_bytes=2_000_000_000)
        record={"source":source,"sha256":checksum,
                "bytes":target.stat().st_size,"signature":"PENDING WINDOWS AUTHENTICODE VERIFICATION"}
        Path(".runtime/ollama-installer.json").write_text(json.dumps(record,indent=2),encoding="utf-8")
        print(json.dumps(record,indent=2),flush=True)
