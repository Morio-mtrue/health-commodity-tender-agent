# Local open-weights model setup

The inspected demo computer has approximately 15.7 GiB RAM. Signed Ollama 0.40.3 is installed and serves the checksum-verified Qwen GGUF on CPU, with cloud disabled. Eight document-scoped workflows (five on 11 October, three on 15 October 2026) completed in 100.78 to 225.00 seconds with simulated approvals; measurements and limitations are in EVALS.md.

The adapters support local Ollama and portable llama.cpp HTTP endpoints. They record model/runtime identity, prompt version, and usage. Remote endpoints, credential URLs, oversized contexts, different served model identities, and truncated output are rejected.

## Pinned portable candidate and observed failure

The official [Qwen GGUF](https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF) Q4_K_M file was downloaded and verified: 1,117,320,736 bytes, revision `91cad51170dc346986eccefdc2dd33a9da36ead9`, publisher LFS SHA-256 `6a1a2eb6d15622bf3c96857206351ba97e1af16c30d7a74ee38970e434e9407e`, Apache 2.0. The official [llama.cpp b11429 CPU archive](https://github.com/ggml-org/llama.cpp/releases/tag/b11429) matched SHA-256 `1283323272b04cd07905816a597a0da810918102de958f4ff6f7bbaa70ed2efe`.

`./scripts/start.ps1 -WithModel` verifies those fixed files, starts a hidden CPU process, checks health, and runs the workbench. Interrupted downloads resume at a checked range and must pass the final checksum. However, this computer's Windows Application Control blocked the runtime DLL with WinError 4551. The first actual MCP model attempt failed after 12.88 seconds, before inference. This provides no model-quality or speed measurement. Security-policy changes are outside setup.

The official Windows installer and installed executable both had valid Ollama Inc. Authenticode signatures. Installer provenance: 1,578,217,944 bytes, SHA-256 `ab81db6c6f4f65547242d1b2912e854da660ab3bc1dbd5ae3483831cf7668c80`. The recorded download SHA is provenance, not an independent publisher checksum; future installers still require valid publisher signatures. [Windows documentation](https://docs.ollama.com/windows).

The existing GGUF is imported as `tender-qwen:1.5b-q4`, manifest digest `2304751c9569070cb5bd3ef97e4f7dd5f769cee5ed635fbd6775ceb62de6b7e6`. Ollama reports parameter_size `1.8B`; this runtime metadata is retained separately from the publisher's Qwen2.5-1.5B model name. The project server uses port 11435, `.runtime/ollama-models`, `OLLAMA_NO_CLOUD=1`, and one inference slot. Other Ollama processes are not configured by the script. Initial Windows GPU discovery took about 96 seconds; readiness now permits 180 bounded attempts.

## Candidate and bake-off

Start with a small quantized model to measure CPU performance before considering larger models. One candidate is `qwen2.5:1.5b`, listed by Ollama at approximately 986 MB, Q4_K_M, Apache 2.0. This is a candidate, not a validated model recommendation. Compare extraction recall and citation accuracy against a stronger model if the machine permits it.

Sources inspected: https://ollama.com/library/qwen2.5:1.5b and https://docs.ollama.com/windows

## Run

1. Run `./scripts/start.ps1 -WithOllama`. This verifies the signed official per-user Windows package, installs it when absent, and imports the pinned GGUF. Installer wait is bounded at ten minutes.
2. Open http://127.0.0.1:8000.
3. Choose the existing synthetic review case or create your own closed-tender case.
4. Create a case using the selected closed tender, all applicable addenda, and synthetic bids.
5. Enter `tender-qwen:1.5b-q4` in extraction settings before compiling the plan.
6. Review and edit the model's sourced manual criteria, then perform the named plan lock yourself.
7. Evaluate the bids, review the findings, and perform the named export approval yourself.

The adapter deliberately limits tender text to 100,000 characters; use a coherent source excerpt for the hackathon. It rejects missing quotations, invented sources, and unsupported weights. Arithmetic cannot be delegated to the model. No OCR is configured in this release.

Ollama uses its documented [JSON-schema output constraint](https://docs.ollama.com/capabilities/structured-outputs), temperature zero, 16,384-token context, CPU execution, and at most 5,000 generated tokens. Inference is bounded at 600 seconds; model compilation transport at 660 seconds. A character limit does not guarantee token-context fit: inspect completeness. Cloud tags and remote aliases are rejected before sending source text.

Prompt `criteria-v4` and output-schema hashes accompany model metadata. Extraction is scoped to one source document per request, with a shared 600-second inference budget. The application binds hashes from the trusted source manifest and displays the validated quoted span. Original tender requests constrain supersedes to null; an addendum must explicitly quote a replacement of the named criterion. Other amendment wording needs human interpretation and cannot automatically deactivate a rule. Raw proposals remain immutable artifacts, including rejected proposals; the accepted proposal accompanies export. Methods remain manual until human review.

```powershell
$env:TENDER_LOCAL_MODEL_URL='http://127.0.0.1:11435'
$env:TENDER_LOCAL_MODEL_BACKEND='ollama'
uv run python -m scripts.model_eval --model tender-qwen:1.5b-q4 --native-text --repeats 5
uv run python -m scripts.prepare_model_review
```

The evaluation command runs simulated gates. The review command creates a fresh actual-model case in the workbench and pauses before human approval.

## Evidence required for submission

Save the complete case package and audit log, model digest, extraction recall, citation accuracy, wall time, human pause time, memory usage, and actual cost. Repeat five model runs. Five deterministic fixture runs are not evidence of model stability. A test approval labelled `TEST SIMULATION` is not a named human approval for the public demo.
