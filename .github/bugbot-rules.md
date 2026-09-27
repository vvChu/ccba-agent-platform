# CCBA Bugbot Automated Review Rules & Platform Invariants

> **Target:** Cursor Bugbot & GitHub Copilot Automated Pull Request Reviewers  
> **Repository:** `vvChu/ccba-agent-platform` (Hub Monorepo)  
> **Role:** Read-Only Static Architectural & Code Quality Auditor  
> **Enforcement Mode:** Read-Only Advisory (Comments & Suggestions only; no auto-merge)

When reviewing any Pull Request diff in this repository, evaluate and flag violations against the following non-negotiable platform rules:

---

## 1. Architectural & Dependency Invariants

* **`[RULE-01] SEAM_REUSE (Platform-Aware KISS)`**:
  * *Check:* Does the PR introduce a new utility script, data parsing function, or helper class that duplicates capabilities already registered in `.agents/skills/platform-loader/catalog.yaml`?
  * *Action:* Flag any ad-hoc script or isolated silo. Demand reuse of public Deep Seams or explicit documented rationale in the PR description.

* **`[RULE-02] DECOUPLED_CONNECTION (No Inverted Coupling)`**:
  * *Check:* Connection layer files (matching `*_client.py`, `ccba_ai/ai.py`, or gateway connectors) must remain pure leaf dependencies.
  * *Action:* Flag any import from higher-level consumers or business logic modules into lower connection packages.

* **`[RULE-03] AST_SPAN_INSPECTION (Contract Bypass Hygiene)`**:
  * *Check:* If a multi-line import statement uses `# ccba:allow-raw-bypass` or `# ccba:allow-machine-path`, does the exemption comment cover the full AST span `[node.lineno, node.end_lineno]`?
  * *Action:* Flag any comment placed on a continuation line that leaves preceding lines unexempted.

---

## 2. Determinism & Multi-OS Invariants

* **`[RULE-04] MULTI_KEY_SORT (Deterministic Negation)`**:
  * *Check:* When sorting collections by mixed criteria (e.g., descending score + ascending name/degree), NEVER use blanket `reverse=True`.
  * *Action:* Mandate mathematical negation with explicit float rounding: `key=lambda x: (-round(x.score, 4), -x.degree, x.name)`.

* **`[RULE-05] INODE_INVARIANCE (Filesystem Determinism)`**:
  * *Check:* Does code ingest files via `os.scandir()` or `Path.glob()` to build lookup tables or resolver maps with potential key collisions?
  * *Action:* Require explicit deterministic sorting by unique stem before map ingestion (e.g., `sorted(Path.glob(...), key=lambda p: p.stem)`).

* **`[RULE-06] POSIX_PERMISSIONS (Permission Preservation)`**:
  * *Check:* When executing `os.chmod()` or atomic file writes, does the code preserve the user execute bit (`stat.S_IXUSR`) if the file was originally executable?
  * *Action:* Flag static `chmod(0o600)` overwriting executable bits on scripts and CLI tools.

* **`[RULE-07] MACHINE_STATE_DECOUPLING (No Leaked Absolute Paths)`**:
  * *Check:* Does the diff contain hardcoded Windows drive paths (e.g., `C:\...`, `D:\...`) or home directory paths?
  * *Action:* Flag hardcoded absolute paths unless marked with `# ccba:allow-machine-path`. Require resolution via environment variables (e.g., `CCBA_HUB_PATH`).

---

## 3. Security, Quality & Testing Invariants

* **`[RULE-08] SECRETS_MASKARA (Zero Hardcoded Secrets)`**:
  * *Check:* Does the diff introduce unmasked API keys (LiteLLM, Gemini, OpenAI, Groq), bearer tokens, private keys, or passwords?
  * *Action:* Immediately flag as CRITICAL security violation. Require environment variable lookup or `ccba_maskara` redaction.

* **`[RULE-09] VERIFIER_TEST_PARITY (ADR-0058 Hard Completion Lock)`**:
  * *Check:* If the PR modifies or adds public functions, Deep Seams, or CLI commands, are corresponding unit tests added or updated in the package's `tests/` directory?
  * *Action:* Flag any PR adding untested logic. Code must pass `python -m ccba_harness verify-patch`.

* **`[RULE-10] ATOMIC_MICRO_PR (Blast Radius Control)`**:
  * *Check:* Is the PR diff larger than 300 lines of code (excluding test fixtures, mock data, and `.md` documentation)?
  * *Action:* Add an advisory note recommending decomposition into atomic tracer-bullet vertical slices ($\le 200$ LOC per PR).
