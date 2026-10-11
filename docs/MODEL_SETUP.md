# Local open-weights model setup

The inspected demo computer has approximately 15.7 GiB RAM. No GPU capability is assumed. No successful open-model workflow has completed yet.

The adapters support local Ollama and portable llama.cpp HTTP endpoints. They record model/runtime identity, prompt version, and usage. Remote endpoints, credential URLs, oversized contexts, different served model identities, and truncated output are rejected.

## Pinned portable candidate and observed failure

The official [Qwen GGUF](https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF) Q4_K_M file was downloaded and verified: 1,117,320,736 bytes, revision `91cad51170dc346986eccefdc2dd33a9da36ead9`, publisher LFS SHA-256 `6a1a2eb6d15622bf3c96857206351ba97e1af16c30d7a74ee38970e434e9407e`, Apache 2.0. The official [llama.cpp b11429 CPU archive](https://github.com/ggml-org/llama.cpp/releases/tag/b11429) matched SHA-256 `1283323272b04cd07905816a597a0da810918102de958f4ff6f7bbaa70ed2efe`.

`./scripts/start.ps1 -WithModel` verifies those fixed files, starts a hidden CPU process, checks health, and runs the workbench. Interrupted downloads resume at a checked range and must pass the final checksum. However, this computer's Windows Application Control blocked the runtime DLL with WinError 4551. The first actual MCP model attempt failed after 12.88 seconds, before inference. This provides no model-quality or speed measurement. Security-policy changes are outside setup.

The user authorized local runtime setup. The standard official Ollama installer is being prepared for Windows Authenticode verification. Its Windows documentation requires at least 4 GB installed, plus weights. The download's recorded SHA is provenance, not an independent publisher checksum. Verify a valid publisher signature before executing it.

Once an approved Ollama runtime is available, import the existing GGUF with a Modelfile containing FROM and its absolute path, then record the installed tag/digest. Alternatively pull the smaller Ollama artifact below, which requires a separate provenance record.

## Candidate and bake-off

Start with a small quantized model to measure CPU performance before considering larger models. One candidate is `qwen2.5:1.5b`, listed by Ollama at approximately 986 MB, Q4_K_M, Apache 2.0. This is a candidate, not a validated model recommendation. Compare extraction recall and citation accuracy against a stronger model if the machine permits it.

Sources inspected: https://ollama.com/library/qwen2.5:1.5b and https://docs.ollama.com/windows

## Run

1. Install the official Ollama Windows runtime following its documentation (a separate local installation).
2. In a terminal, run `ollama pull qwen2.5:1.5b`.
3. Start the workbench with `./scripts/start.ps1`.
4. Create a case using the selected closed tender, all applicable addenda, and synthetic bids.
5. Enter the exact installed model tag in extraction settings before compiling the plan.
6. Review and edit the model's sourced manual criteria, then perform the named plan lock yourself.
7. Evaluate the bids, review the findings, and perform the named export approval yourself.

The adapter deliberately limits tender text to 100,000 characters; use a coherent source excerpt for the hackathon. It rejects missing quotations, invented sources, and unsupported weights. Arithmetic cannot be delegated to the model. No OCR is configured in this release.

## Evidence required for submission

Save the complete case package and audit log, model digest, extraction recall, citation accuracy, wall time, human pause time, memory usage, and actual cost. Repeat five model runs. Five deterministic fixture runs are not evidence of model stability. A test approval labelled `TEST SIMULATION` is not a named human approval for the public demo.
