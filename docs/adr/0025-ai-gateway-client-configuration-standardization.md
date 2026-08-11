# 25. Standardizing AI Gateway Client Configuration and Model Aliases

Date: 2026-08-11
Status: Approved

## Context
During the document review and grilling process (`/ccba-grill-with-docs`), inconsistencies were identified across environment templates, SDK settings, and service configurations regarding AI Gateway access points, local GPU model alias naming, secret exposure risks, and RAG virtual alias usage.

## Decisions

1. **AI Gateway Endpoint Standardization**:
   - All AI integrations MUST use `AI_GATEWAY_URL=http://100.83.192.30:8090/v1` and `AI_GATEWAY_KEY`.
   - Direct bypass to vLLM ports (e.g., port 8004) is prohibited in application layer code; all calls must flow through the central LiteLLM AI Gateway for auditing, fallback, and rate limiting.

2. **Model Alias Refactoring**:
   - The legacy, unmapped model string `qwen3.5-35b` is completely deprecated and removed across all configs and codebase defaults.
   - The primary local GPU model alias is standardized as `qwen-local-primary` (or version-specific `qwen-3.5-35b`).

3. **Secret Hygiene**:
   - All `.env.example` templates (`input_documents/.env.example`, root `.env.example`) must remain sanitized with no raw API keys committed.

4. **RAG Virtual Aliases Integration**:
   - Platform packages (`mdconverter`, `ccba-pdf-prep`, `ccba-ai`) will embed RAG Virtual Aliases (`ocr-primary`, `rag-core`, etc.) as standard default settings to maximize Free Tier Farm utilization.

## Consequences
- Prevents `404 Model Not Found` runtime exceptions when invoking local LLMs.
- Ensures uniform security compliance across all platform spokes and tools.
- Optimizes API throughput and latency by directing vision/RAG tasks to designated gateway virtual aliases.
