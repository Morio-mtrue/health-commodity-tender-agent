"""Download selected official sources locally; no datasets are redistributed."""
import hashlib
import json
from pathlib import Path
import httpx

URLS = {
    "original-tender.pdf": "https://kemsa.go.ke/download/file/747e605cfecae01cf9a53102136d681d.pdf",
    "extension-notice.pdf": "https://kemsa.go.ke/download/file/a85fa50f20d8655dd811155fb22b34d2.pdf",
}

if __name__ == "__main__":
    root=Path("local_data/kemsa-oit05-2024-2026")
    root.mkdir(parents=True,exist_ok=True)
    result=[]
    with httpx.Client(timeout=25,follow_redirects=False) as client:
        for name,url in URLS.items():
            try:
                response=client.get(url)
                response.raise_for_status()
                if not response.content.startswith(b"%PDF-") or len(response.content)>25_000_000:
                    raise ValueError("Invalid PDF or size limit exceeded")
                (root/name).write_bytes(response.content)
                result.append({"name":name,"source_url":url,"sha256":hashlib.sha256(response.content).hexdigest(),"status":"DOWNLOADED"})
            except Exception as error:
                result.append({"name":name,"source_url":url,"status":"SOURCE_UNAVAILABLE","error":str(error)})
    (root/"retrieval.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
    print(json.dumps(result,indent=2))
