# 29. AI Gateway Client Integration Contract & 4 Model Archetypes Standardization

Date: 2026-08-14
Status: Approved

## Context
Following the deployment of AI Gateway on Server Spark with Fallback Cascade across 10 keys and multi-tier routing (cloud down to local vLLM Qwen 35B), client applications required a unified integration contract. In particular, client calls previously lacked explicit HTTP timeout guards (leading to premature disconnections during gateway failover) and used unstandardized model names across packages and skills.

## Decisions

1. **Mandatory HTTP Timeout Contract**:
   - All AI Gateway client instances (`AIClient`, `AsyncAIClient`, raw `OpenAI`, `httpx`, `fetch`) MUST configure `timeout >= 30.0s` (standard default: `60.0s`).
   - Configurable via `AI_GATEWAY_TIMEOUT` environment variable.
   - Prevents client-side connection drops while Gateway executes graceful multi-key failover and model downgrade.

2. **4 Standard Model Archetypes**:
   - **Archetype 1: OCR & Vision Ingestion**: `ocr-primary`, `ocr-fallback`, `ocr-tier4` (Direct Google AI Studio 10 keys).
   - **Archetype 2: Standard General / Coding**: `gemini-3.7-flash`, `gemini-3.7-flash-medium`, `text-gemma` (Google API + Proxy).
   - **Archetype 3: Deep Reasoning / Complex Audit**: `gemini-3.7-flash-high`, `claude-sonnet-4-6-thinking`, `reasoning-gemma`.
   - **Archetype 4: Local Private / Zero-Cost**: `rag-core`, `qwen-local-primary` (vLLM Qwen 35B Local GPU DGX).

3. **Zero-Config Thinking Parameters**:
   - Client applications MUST NOT manually construct `generationConfig.thinking_config` or `thinking_budget`.
   - The Gateway's internal preprocessor (`custom_callbacks.gemini_corrector`) automatically parses suffixes (`-low`, `-medium`, `-high`) and manages token budgets.

4. **Modular Routing Architecture**:
   - Model constants and routing helpers are encapsulated in [`ccba_ai.routing`](../../packages/ccba-ai/src/ccba_ai/routing.py) preserving Deep Module principles.

## Consequences
- Guarantees 99.9% uptime resilience via transparent Fallback Cascade.
- Eliminates hardcoded deprecated model strings across Hub packages (`ccba-ai`, `mdconverter`, `ccba-legal-intel`, `ccba-pdf-prep`) and Agent skills (`qc-discovery`, `batch-orchestrator`, `design`).
- Ensures consistency across Python, TypeScript/Web, and CLI clients.
