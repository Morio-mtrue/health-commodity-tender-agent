"""Download selected official sources locally; no datasets are redistributed."""
import hashlib
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
import httpx

URLS = {
    "original-tender.pdf": "https://kemsa.go.ke/download/file/747e605cfecae01cf9a53102136d681d.pdf",
    "extension-notice.pdf": "https://kemsa.go.ke/download/file/a85fa50f20d8655dd811155fb22b34d2.pdf",
    "addendum-1.pdf": "https://kemsa.go.ke/download/file/cdf1c6c2bd8e468a3843cd45f1181ff7.pdf",
    "addendum-2.pdf": "https://kemsa.go.ke/download/file/49dfc23a66ba0983f8798f6db435a7a9.pdf",
}

if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--only",nargs="+",choices=URLS)
    names=parser.parse_args().only or list(URLS)
    root=Path("local_data/kemsa-oit05-2024-2026")
    root.mkdir(parents=True,exist_ok=True)
    result=[]
    with httpx.Client(timeout=25,follow_redirects=False) as client:
        for name,url in URLS.items():
            if name not in names:
                continue
            record={"name":name,"source_url":url,"attempted_at":datetime.now(timezone.utc).isoformat()}
            try:
                data=bytearray()
                with client.stream("GET",url) as response:
                    response.raise_for_status()
                    for chunk in response.iter_bytes(65536):
                        data.extend(chunk)
                        if len(data)>25_000_000:
                            raise ValueError("PDF size limit exceeded")
                if not data.startswith(b"%PDF-"):
                    raise ValueError("Invalid PDF or size limit exceeded")
                (root/name).write_bytes(data)
                result.append({**record,"sha256":hashlib.sha256(data).hexdigest(),"bytes":len(data),"status":"DOWNLOADED"})
            except Exception as error:
                result.append({**record,"status":"SOURCE_UNAVAILABLE","error":str(error)})
    (root/"retrieval.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
    print(json.dumps(result,indent=2))
