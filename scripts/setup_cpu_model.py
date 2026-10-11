"""Project-local portable runtime and Apache-licensed model; no system installation."""
import hashlib
import json
import re
import zipfile
from pathlib import Path
import httpx

RUNTIME_URL="https://github.com/ggml-org/llama.cpp/releases/download/b11429/llama-b11429-bin-win-cpu-x64.zip"
RUNTIME_SHA="1283323272b04cd07905816a597a0da810918102de958f4ff6f7bbaa70ed2efe"
REPOSITORY="Qwen/Qwen2.5-1.5B-Instruct-GGUF"
MODEL="qwen2.5-1.5b-instruct-q4_k_m.gguf"
MODEL_REVISION="91cad51170dc346986eccefdc2dd33a9da36ead9"
MODEL_SHA="6a1a2eb6d15622bf3c96857206351ba97e1af16c30d7a74ee38970e434e9407e"


def download(client,url,path,expected=None,max_bytes=1_300_000_000):
    if path.exists():
        existing=hashlib.sha256()
        with path.open("rb") as input_file:
            for block in iter(lambda:input_file.read(1024*1024),b""):
                existing.update(block)
        existing_digest=existing.hexdigest()
        if not expected or existing_digest==expected:
            return existing_digest
    partial=path.with_suffix(path.suffix+".part")
    for attempt in range(3):
        total=partial.stat().st_size if partial.exists() else 0
        hasher=hashlib.sha256()
        if total:
            with partial.open("rb") as previous:
                for block in iter(lambda:previous.read(1024*1024),b""):
                    hasher.update(block)
            print(f"Resuming {path.name} at {total//(1024*1024)} MiB",flush=True)
        try:
            with client.stream("GET",url,headers={"Range":f"bytes={total}-"} if total else {}) as response:
                response.raise_for_status()
                if total and response.status_code==206:
                    if not response.headers.get("content-range","").startswith(f"bytes {total}-"):
                        raise ValueError("Server returned a different download range")
                    mode="ab"
                else:
                    total=0
                    hasher=hashlib.sha256()
                    mode="wb"
                with partial.open(mode) as output:
                    for block in response.iter_bytes(1024*1024):
                        total+=len(block)
                        if total>max_bytes:
                            raise ValueError("Download exceeds the size limit")
                        output.write(block)
                        hasher.update(block)
                        if total//(64*1024*1024)!=(total-len(block))//(64*1024*1024):
                            print(f"{path.name}: {total//(1024*1024)} MiB",flush=True)
            break
        except httpx.TransportError:
            if attempt==2:
                raise
            print("Transfer interrupted; retrying the verified partial download",flush=True)
    result=hasher.hexdigest()
    if expected and result!=expected:
        raise ValueError("Official download checksum mismatch")
    partial.replace(path)
    return result


def main():
    root=Path(".runtime").resolve()
    root.mkdir(exist_ok=True)
    with httpx.Client(timeout=60,follow_redirects=True) as client:
        print("Downloading verified official CPU runtime…",flush=True)
        runtime_hash=download(client,RUNTIME_URL,root/"llama-cpu.zip",RUNTIME_SHA,100_000_000)
        runtime=root/"llama"
        runtime.mkdir(exist_ok=True)
        with zipfile.ZipFile(root/"llama-cpu.zip") as archive:
            for item in archive.infolist():
                if not (runtime/item.filename).resolve().is_relative_to(runtime) or ((item.external_attr>>16)&0o170000)==0o120000:
                    raise ValueError("Unsafe runtime archive path")
            archive.extractall(runtime)
        # Revision and LFS checksum were verified against the official model metadata.
        # Keep them fixed so later startup cannot silently change the evaluated model.
        commit,expected=MODEL_REVISION,MODEL_SHA
        model_root=Path("models").resolve()
        model_root.mkdir(exist_ok=True)
        print("Downloading pinned Qwen 1.5B Q4_K_M weights…",flush=True)
        model_hash=download(client,f"https://huggingface.co/{REPOSITORY}/resolve/{commit}/{MODEL}",model_root/MODEL,expected)
        manifest={"runtime":"llama.cpp","runtime_version":"b11429","runtime_sha256":runtime_hash,
                  "runtime_source":RUNTIME_URL,"model_repository":REPOSITORY,"model_revision":commit,
                  "model_filename":MODEL,"model_sha256":model_hash,"licence":"Apache-2.0",
                  "model_path":str(model_root/MODEL)}
        (root/"model-manifest.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
        print(json.dumps(manifest,indent=2),flush=True)


if __name__=="__main__":
    main()
