# ccba-ai Package Guidance

Unified client library connecting to the LiteLLM AI Gateway on Server Spark.

- **Public Deep Seams**: `from ccba_ai import ai, AIClient, AsyncAIClient, AntigravityCLIProvider, CopilotCLIProvider, PersistentStdioDaemon, xml_envelope, parse_xml_tags, evaluator_optimizer_loop`.
- **Contracts**: All clients MUST configure `timeout >= 30.0s`. Zero-config thinking params (use suffixes `-low`, `-medium`, `-high`). Tier 3 Dual-CLI fallback prioritizes by Model-Family Affinity (OpenAI -> Copilot, Gemini -> Antigravity) with Cross-CLI failover.
- **Scoped Tests**: `pytest packages/ccba-ai/tests`
