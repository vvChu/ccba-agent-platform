# ccba-ai Package Guidance

Unified client library connecting to the LiteLLM AI Gateway on Server Spark.

- **Public Deep Seams**: `from ccba_ai import ai, AIClient, AsyncAIClient`, `ccba_ai.routing`, `ccba_ai.prompting` (`xml_envelope`, `parse_xml_tags`, `evaluator_optimizer_loop`).
- **Contracts**: All clients MUST configure `timeout >= 30.0s`. Zero-config thinking params (use suffixes `-low`, `-medium`, `-high`).
- **Scoped Tests**: `pytest packages/ccba-ai/tests`
