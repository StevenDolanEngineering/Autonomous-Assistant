# Autonomous Assistant ("Otto")

Otto is a local-first, autonomous background context engine designed to serve as the intelligent "brain" for assistive technologies. Its primary integration targets include
[Assistive-AAC-Prototype](https://github.com/StevenDolanEngineering/Assistive-AAC-Prototype).

Built to operate entirely on-device, Otto ensures absolute user privacy and 100% offline reliability—critical requirements for dependable medical and assistive communication hardware.

## 🌟 The Philosophy: Local-First & Private

For users relying on assistive communication devices, internet dependency is a vulnerability. Otto operates under strict architectural constraints:
- **100% Offline Functionality:** No internet connection required. All processing occurs on the local CPU/GPU.
- **Absolute Privacy:** User data, conversations, and environmental context never leave the local device hardware.
- **Zero Operating Costs:** Eliminates reliance on external cloud APIs, preventing recurring API tolling.

## 🧠 System Architecture & Role

Otto runs as a background service, communicating with the frontend interface via a local, low-latency WebSocket or local REST API loop.

## 🛠️ Planned Core Features

- **Predictive Context Layer:** Analyzes local device state (time, calendar entries, basic sensor inputs) to dynamically predict and bubble up relevant AAC phrases.
- **Local Intent Parsing:** Translates user intent selections into specific local device actions (e.g., smart home API triggers or system audio settings) via tool calling.
- **Deterministic Guardrails:** Wraps local LLM outputs in strict JSON schema validation to guarantee reliable UI updates without hallucinations.

## 🚀 Quickstart (Development Status: Experimental)

*Note: This repository is in active development as we map out the local integration pipeline.*

### Target Runtime Environment
- **LLM Engine:** [Ollama](https://ollama.com) or [LlamaEdge](https://llamaedge.com) running lightweight open-source weights (e.g., Llama-3-8B-Instruct-Q4 or Phi-3-mini).
- **Communication:** Python/Node.js background process hosting a local server loop.

## 🛣️ Roadmap

- [x] Establish local-only background daemon structure.
- [ ] Implement local WebSocket server for zero-network-lag messaging.
- [ ] Connect a 1B–3B parameter quantized open-source LLM for predictive testing.
- [ ] Standardize the communication JSON schema between Otto and the AAC frontend interface.
