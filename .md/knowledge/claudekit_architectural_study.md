# ClaudeKit-Engineer: Complete Architectural Study & Technical Reference

## Executive Summary

This study provides a comprehensive architectural analysis of the **ClaudeKit-Engineer** platform, focusing on its event-driven lifecycle hook system, its multi-agent orchestration model, and the detailed mechanics of its 87 custom skill modules. The study evaluates these architectural elements in the context of the **ccba-agent-platform** to extract actionable design patterns, technical improvements, and integration opportunities.

ClaudeKit-Engineer operates as a modular, event-driven development platform built on top of Claude Code. It employs:
1. **Event-Driven Hook Lifecycle**: Intercepts shell, tool, prompt, and session actions using Node.js wrappers that consume and output JSON via standard input/output streams.
2. **Multi-Agent Orchestration**: Organizes development milestones using Markdown-defined agent personas, centralized task lists, and file-based roadmaps (`plan.md` and phase stubs) that prevent state corruption across context compactions.
3. **Progressive Disclosure Skills**: Standardizes tool extensions using metadata manifests, brief instruction files (SKILL.md), and on-demand reference directories to minimize model context overhead.

---

## Part 1: The Hook Lifecycle System

ClaudeKit-Engineer's hook system is designed to intercept and govern every major phase of the agent's execution lifecycle. The system is configured via `claude/settings.json` and implemented using Node.js scripts in `claude/hooks/`.

### 1. Settings Configuration and Entrypoints

The hook system maps specific events to executable Node scripts. The primary entrypoints and their behaviors include:

- **`SessionStart`**: Triggers on `startup`, `resume`, `clear`, or `compact`. Runs `session-init.cjs` and `usage-quota-cache-refresh.cjs` to establish session IDs, locate workspace Git roots, purge shadowed temporary folders, and display status logs.
- **`UserPromptSubmit`**: Intercepts all incoming user messages. Runs `simplify-gate.cjs` (to block oversized changes), `dev-rules-reminder.cjs` (to inject standard formatting guidelines), and `usage-quota-cache-refresh.cjs`.
- **`SubagentStart`**: Intercepts subagent spawning. Runs `subagent-init.cjs` to inject active plans, coding styles, language targets, and Python virtual environment contexts into child agent prompts.
- **`PreToolUse`**: Intercepts tool calls before execution.
  - Matches `Write` tool: runs `descriptive-name.cjs` to enforce snake_case (Python), kebab-case (JS/TS), or PascalCase (Java) conventions.
  - Matches `Bash|Glob|Grep|Read|Edit|Write` tools: runs `scout-block.cjs` (enforces `.ckignore` rules) and `privacy-block.cjs` (intercepts access to `.env` or credential files, requiring user-approved `APPROVED:` prefixes).
- **`PostToolUse`**: Intercepts tool execution outputs.
  - Matches `Edit|Write|MultiEdit`: runs `plan-format-kanban.cjs` to check plan file syntax.
  - Matches `Task|TaskCreate|TaskUpdate|TodoWrite`: runs `session-state.cjs` to refresh progress snapshots.
- **`SubagentStop`**: Triggers when a subagent finishes. Runs `cook-after-plan-reminder.cjs` (for planning subagents) and `session-state.cjs` to append results to the global progress markdown log.
- **`Stop`**: Triggers on session termination. Runs `session-state.cjs` to compile the final session summary report (`latest.md`), package touched file lists using Git diff, and rotate session logs.

### 2. Core Hook Scripts Walkthrough

All hook scripts follow a **fail-open** policy (returning exit code `0` on non-critical errors) to ensure the developer interface remains functional even if a check script fails. Interactive blocks (like privacy prompts) exit with code `2` to halt execution.

- **`session-init.cjs`**: Sets environment variables (`CK_SESSION_ID`, `CK_ACTIVE_PLAN`, `CK_GIT_ROOT`) and writes them to the file defined by `CLAUDE_ENV_FILE`. It restores the previous state from `latest.md` and alerts the LLM if context compaction occurred to avoid bypassing pending approvals.
- **`simplify-gate.cjs`**: Enforces code churn limits. Scans git status and diffs. If the lines of code (LOC) changed exceed thresholds (e.g., > 400 LOC total or > 200 LOC in a single file), it blocks finalization commands until a simplifier agent runs.
- **`dev-rules-reminder.cjs`**: Uses a rate-limiting helper (`context-builder.cjs`) to inject guidelines into user prompts without overwhelming the context window on rapid consecutive inputs.
- **`usage-quota-cache-refresh.cjs`**: Queries usage logs to display runtime cosmetic stats on the shell statusline. Fetches are throttled (5m for tools, 1m for prompts) to prevent API rate limits.
- **`subagent-init.cjs`**: Injects a compact (~200 tokens) guideline into child agents containing active plans, file paths, project types, and the active virtual environment python path.
- **`descriptive-name.cjs`**: Warns against generic file names (e.g., `test.txt`, `report.md`) and prompts the agent to use descriptive, context-specific names.
- **`scout-block.cjs`**: Reads `.ckignore` parameters and blocks access to ignored folders (like `node_modules` or build outputs) while allowing compilation commands to execute.
- **`privacy-block.cjs`**: Prevents the agent from reading secret keys or certificates. If a protected file is touched, the agent must ask the user for permission, then bypass the block by prefixing the path with `APPROVED:`.
- **`plan-format-kanban.cjs`**: Validates the visual structure of `./plan.md` tables and relative phase links, encouraging the use of CLI plan tools over manual edits.
- **`session-state.cjs`**: Serializes active tasks, updates statusline caches, maps modified files, and rotates local session history archives.
- **`cook-after-plan-reminder.cjs`**: Suggests next steps (validate, red-team, cook) to the developer when a plan design subagent completes.
- **`workflow-artifact-gate.cjs`**: Evaluates files in the active staging directory against rules for the current workflow stage. Blocks finalizing/shipping commands if artifacts are malformed.

---

## Part 2: The Multi-Agent Orchestration Model

ClaudeKit-Engineer implements a multi-agent model to coordinate complex tasks across specialized personas.

### 1. Agent Definition Format

Agent personas are defined in Markdown files inside `claude/agents/`. Each file contains:
- **YAML Frontmatter Configuration**: Details the agent's name, description (with XML examples explaining its role to the orchestrator), target model, memory limits, and tool permissions.
- **System Instructions**: Defines the persona (e.g., Senior Systems Architect, Security Auditor), checklists (verification checks, error bounds), responsibilities (YAGNI/KISS), naming conventions, and Team Mode instructions.

### 2. Multi-Agent Coordination Mechanics

Coordination is built around a **Task-based model** managed by the main orchestrator:
- **Subagent Spawning**: The main agent calls the `Task` tool (`Task(subagent_type, prompt, description)`).
- **Shared Workspace**: Subagents read tasks (`TaskList`), claim tasks by setting them to in-progress (`TaskUpdate`), and report completion.
- **Communication Channels**: Subagents communicate via `SendMessage` to send status updates and request shutdowns (`shutdown_request`, `shutdown_response`).
- **Standardized Reports**: Finished subagents write structured reports to the reports folder (`{reports-dir}/{agent-type}-{namePattern}-[purpose]-report.md`).

### 3. File-Based Planning (`plan.md` & `phase-XX-*.md`)

State loss during LLM context compaction is solved by storing planning states in persistent Markdown files:
- **`plan.md`**: Central roadmap starting with YAML metadata (title, status, priority, branch, dependencies like `blockedBy` or `blocks`) and a 3-column index table (`| Phase | Name | Status |`).
- **`phase-XX-*.md`**: Phase-specific stubs detailing requirements, architecture, related files, steps, success criteria, and risk assessments.
- **CLI Synchronization**: Status updates are performed via deterministic commands (`ck plan check <phase-id> --start`, `ck plan check <phase-id>`) rather than raw string edits to prevent table corruption.
- **Isolation Boundaries**: Phases define explicit file ownership lists. Concurrently running phases must have mutually exclusive lists to prevent conflict.

### 4. Session State Maintenance

Session states are maintained using two synchronized channels:
- **Global Session Progress (`latest.md`)**: Saved in `~/.claude/session-states/{hash}/` (MD5 of working directory). It compiles task statuses, test results, and file changes. During startup, `session-init.cjs` reads and outputs it to the console, restoring the LLM's context. Up to 5 rotating logs are kept in `archive/` with a 7-day expiration.
- **Temporary Session JSON**: Stored in the OS temp directory. Tracks active plans, suggested plans, and statusline activity metadata.

---

## Part 3: Individual Skill Analyses

This section provides an individual analysis of the 87 skill directories found in `claudekit-engineer/claude/skills/`.

### 1. `_shared`
- **Category**: Infrastructure / Shared Utilities
- **Core Purpose**: Central repository for shared libraries, references, and validation standards.
- **Instruction Summary**: Serves as a library for planning models and validation rules.
- **Dependencies/Scripts/Hooks**: Includes `lib/plan-table-parser.cjs` (parses 7 plan formats) and `references/workflow-artifacts.md`.
- **Value to `ccba-agent-platform`**: Reusable parser for setup roadmaps and risk gates.

### 2. `agent-browser`
- **Category**: `dev-tools`
- **Core Purpose**: Automates headless or cloud browser sessions (Playwright/Chrome via CDP) for testing and scraping.
- **Instruction Summary**: Controls automated browsers without using the developer's real profile.
- **Dependencies/Scripts/Hooks**: Integrates with Browserbase, Vercel Sandbox, and AWS Bedrock AgentCore.
- **Value to `ccba-agent-platform`**: Automates E2E testing on web dashboards and crawls local legal sites.

### 3. `agentize`
- **Category**: `dev-tools`
- **Core Purpose**: Converts codebases into agent-friendly monorepos with core packages, CLI wrappers, and MCP servers.
- **Instruction Summary**: Templates codebases to follow agent-centric design principles.
- **Dependencies/Scripts/Hooks**: Delegates to `ck:project-management` and `ck:scout`.
- **Value to `ccba-agent-platform`**: Standardizes packaging of Vietnamese law parsers and custom tools into MCP servers.

### 4. `ai-artist`
- **Category**: `ai-ml`
- **Core Purpose**: Generates product mockups, branding assets, and marketing visuals using prompt templates.
- **Instruction Summary**: Drives image prompt validation through search, creative, and wild modes.
- **Dependencies/Scripts/Hooks**: Runs `scripts/core.py` (BM25 search engine) and `scripts/generate.py`.
- **Value to `ccba-agent-platform`**: Generates high-quality placeholder diagrams and slide graphics for seminars.

### 5. `ai-multimodal`
- **Category**: `ai-ml`
- **Core Purpose**: Analyzes media files (images, audio, video, PDFs) and generates media using Gemini, Imagen, and MiniMax.
- **Instruction Summary**: Manages batch vision checks, audio transcriptions, and document conversions to markdown.
- **Dependencies/Scripts/Hooks**: Python packages `google-genai`, `pillow`. Scripts: `scripts/gemini_batch_process.py` and `scripts/document_converter.py`.
- **Value to `ccba-agent-platform`**: OCR parsing for scanned Vietnamese legal PDFs and transcribing audio meetings.

### 6. `ask`
- **Category**: `utilities`
- **Core Purpose**: Answers technical and architectural questions using a Systems Architect persona.
- **Instruction Summary**: Focuses on trade-offs, boundaries, and scalability following KISS/YAGNI.
- **Dependencies/Scripts/Hooks**: Reads local architectural docs and delegates to `ck:scout`.
- **Value to `ccba-agent-platform`**: Evaluates new Spoke integrations and proposed architectural expansions.

### 7. `backend-development`
- **Category**: `backend`
- **Core Purpose**: Engineering checklists for REST/GraphQL APIs, OWASP security, database performance, caching, and Docker.
- **Instruction Summary**: Standardizes API design and backend verification.
- **Dependencies/Scripts/Hooks**: Contains 11 reference documents (e.g., `backend-api-design.md`, `backend-security.md`).
- **Value to `ccba-agent-platform`**: Design blueprints for building secure, high-performance backends (NestJS/FastAPI).

### 8. `better-auth`
- **Category**: `backend`
- **Core Purpose**: Sets up TypeScript auth using Better Auth, supporting OAuth, passkeys, TOTP, and organizations.
- **Instruction Summary**: Scaffolds auth adapters, schemas, and sessions.
- **Dependencies/Scripts/Hooks**: CLI `better-auth`. Script: `scripts/better_auth_init.py`.
- **Value to `ccba-agent-platform`**: Standardizes secure tenant-based authentication for the management console.

### 9. `bootstrap`
- **Category**: `utilities`
- **Core Purpose**: Scaffolds new projects, maps tech stacks, and executes bootstrapping plans.
- **Instruction Summary**: Guides workspace creation across 4 workflow modes.
- **Dependencies/Scripts/Hooks**: Delegates to `git-manager`, `ck:plan`, and `ck:cook`.
- **Value to `ccba-agent-platform`**: Automatically scaffolds new Spoke workspaces using uniform folder layouts.

### 10. `brainstorm`
- **Category**: `utilities`
- **Core Purpose**: Evaluates technical ideas using problem-first validation and trade-off matrices.
- **Instruction Summary**: Guides developers to challenge unstated assumptions before writing code.
- **Dependencies/Scripts/Hooks**: References `references/problem-first.md`.
- **Value to `ccba-agent-platform`**: Vets feature requests and enforces simplicity to prevent unnecessary features.

### 11. `chrome-profile`
- **Category**: `dev-tools`
- **Core Purpose**: Automates browser sessions using a real Chrome user profile via Chrome DevTools MCP.
- **Instruction Summary**: Locates Chrome profile directories and executes browser controls.
- **Dependencies/Scripts/Hooks**: Python CLI `scripts/chrome_profile_cli.py`.
- **Value to `ccba-agent-platform`**: Allows agents to run automated browser jobs with active developer credentials.

### 12. `ck-autoresearch`
- **Category**: `utilities`
- **Core Purpose**: Concept anchor for autonomous research and iterative optimization loops.
- **Instruction Summary**: Outlines Karpathy's Modify-Verify-Rollback pattern.
- **Dependencies/Scripts/Hooks**: Maps commands `/ck:loop`, `/ck:predict`, `/ck:scenario`, and `/ck:security`.
- **Value to `ccba-agent-platform`**: Defines safety guardrails (verification scripts, commit boundaries) for autonomous workflows.

### 13. `ck-code-review`
- **Category**: `utilities`
- **Core Purpose**: Evaluates specification compliance, code quality, and test coverage.
- **Instruction Summary**: Reviews commits and PR files using structured checklists.
- **Dependencies/Scripts/Hooks**: Contains 12 reference check documents.
- **Value to `ccba-agent-platform`**: Automated pre-commit quality gate to prevent structural errors.

### 14. `ck-debug`
- **Category**: `utilities`
- **Core Purpose**: Systematic root cause diagnosis that requires proving a bug before applying a fix.
- **Instruction Summary**: Guides developers through call stacks, test bisecting, and database locks.
- **Dependencies/Scripts/Hooks**: Script: `scripts/find-polluter.sh` (bisects test pollution).
- **Value to `ccba-agent-platform`**: Speeds up diagnosing failing test runs and API bottlenecks.

### 15. `ck-graphify`
- **Category**: `dev-tools`
- **Core Purpose**: Generates AST-based code graphs and exposes them as a queryable MCP server.
- **Instruction Summary**: Analyzes repository structures to map imports and classes.
- **Dependencies/Scripts/Hooks**: Python package `graphifyy`.
- **Value to `ccba-agent-platform`**: Indexes large multi-package workspaces to trace dependencies.

### 16. `ck-loop`
- **Category**: `utilities`
- **Core Purpose**: Optimizes codebase metrics (lint errors, test coverage, bundle size) over N iterations.
- **Instruction Summary**: Automates the commit-on-success and rollback-on-failure loop.
- **Dependencies/Scripts/Hooks**: References `references/autonomous-loop-protocol.md`.
- **Value to `ccba-agent-platform`**: Automates cleanup tasks like resolving TypeScript errors or formatting styles.

### 17. `ck-plan`
- **Category**: `utilities`
- **Core Purpose**: Scaffolds multi-phase implementation roadmaps using ClaudeKit CLI.
- **Instruction Summary**: Manages planning files and triggers validation/red-team reviews.
- **Dependencies/Scripts/Hooks**: ClaudeKit CLI `ck plan` commands.
- **Value to `ccba-agent-platform`**: Enforces structured plan generation for Spoke deployments.

### 18. `ck-predict`
- **Category**: `utilities`
- **Core Purpose**: Debates proposed code modifications among 5 expert personas.
- **Instruction Summary**: Analyzes potential architecture, security, and performance risks.
- **Dependencies/Scripts/Hooks**: References `references/chain-modes.md` (`--chain reason/probe`).
- **Value to `ccba-agent-platform`**: Identifies system risks before modifying core packages (like `ccba-ai`).

### 19. `ck-scenario`
- **Category**: `utilities`
- **Core Purpose**: Generates edge-case scenarios and QA test plans across 12 axes.
- **Instruction Summary**: Stress-tests features for timing, concurrency, and validation limits.
- **Dependencies/Scripts/Hooks**: References `references/saturation-loop.md`.
- **Value to `ccba-agent-platform`**: Scaffolds test suites for complex webhook handlers and auth routes.

### 20. `ck-security`
- **Category**: `utilities`
- **Core Purpose**: Audits codebases using STRIDE and OWASP threat models.
- **Instruction Summary**: Identifies exposed credentials and supply chain vulnerabilities.
- **Dependencies/Scripts/Hooks**: Runs dependency auditors (`npm audit`, `pip-audit`).
- **Value to `ccba-agent-platform`**: Scans custom packages to prevent hardcoded credentials.

### 21. `coding-level`
- **Category**: `utilities`
- **Core Purpose**: Adapts response explanations based on user experience level.
- **Instruction Summary**: Configures the `codingLevel` flag in `.claude/.ck.json`.
- **Dependencies/Scripts/Hooks**: Modifies local settings files.
- **Value to `ccba-agent-platform`**: Tailors agent communication detail for junior vs. senior developers.

### 22. `common`
- **Category**: Infrastructure / Shared Utilities
- **Core Purpose**: Helper library for Gemini API key validation and rotation.
- **Instruction Summary**: Standardizes client configuration and handles key failures.
- **Dependencies/Scripts/Hooks**: Scripts: `api_key_helper.py` and `api_key_rotator.py`.
- **Value to `ccba-agent-platform`**: Blueprint for the platform's API Gateway multi-key rotation system.

### 23. `context-engineering`
- **Category**: `utilities`
- **Core Purpose**: Optimizes token consumption and manages LLM context windows.
- **Instruction Summary**: Analyzes context budgets, KV-cache utilization, and attention curves.
- **Dependencies/Scripts/Hooks**: Python scripts: `context_analyzer.py` and `compression_evaluator.py`.
- **Value to `ccba-agent-platform`**: Prevents token bloat and optimizes long prompts in the `ccba-ai` package.

### 24. `cook`
- **Category**: `utilities`
- **Core Purpose**: Orchestrates feature development and bug fixes using structured phases.
- **Instruction Summary**: Enforces Scout -> Plan -> Cook -> Review -> Test -> Finalize workflows.
- **Dependencies/Scripts/Hooks**: Integrates with `ck:project-management` and the `code-reviewer` subagent.
- **Value to `ccba-agent-platform`**: Standard workflow for autonomous coding tasks.

### 25. `copywriting`
- **Category**: `utilities`
- **Core Purpose**: Provides templates and copywriting frameworks (AIDA, PAS) for marketing content.
- **Instruction Summary**: Extracts writing styles from sample files to generate text.
- **Dependencies/Scripts/Hooks**: Python script: `scripts/extract-writing-styles.py`.
- **Value to `ccba-agent-platform`**: Automates notification templates and report summaries.

### 26. `cti-expert`
- **Category**: `security`
- **Core Purpose**: Cyber Threat Intelligence (CTI) and OSINT research helper.
- **Instruction Summary**: Reconnaissance tool for domains, metadata, and data breaches.
- **Dependencies/Scripts/Hooks**: Techniques directory for geolocation and metadata parsing.
- **Value to `ccba-agent-platform`**: Monitors security risks and checks for leaked project assets online.

### 27. `databases`
- **Category**: `database`
- **Core Purpose**: Guides database schema design, index optimization, and migrations.
- **Instruction Summary**: Manages query plans (Postgres EXPLAIN) and Mongo aggregation pipelines.
- **Dependencies/Scripts/Hooks**: Python scripts: `db_migrate.py`, `db_backup.py`, `db_performance_check.py`.
- **Value to `ccba-agent-platform`**: Automatically checks and migrates SQLite/Postgres schemas during updates.

### 28. `deploy`
- **Category**: `infrastructure`
- **Core Purpose**: Deploys applications to 15+ cloud hosting providers.
- **Instruction Summary**: Auto-detects project stack configurations to deploy them.
- **Dependencies/Scripts/Hooks**: Configuration files in `references/platforms/`.
- **Value to `ccba-agent-platform`**: Automates deployment of Spoke APIs to Cloud Run or Vercel.

### 29. `design`
- **Category**: `frontend`
- **Core Purpose**: Designs SVG graphics, interactives, logos, and slide decks.
- **Instruction Summary**: Injects vector styling templates and slide generators.
- **Dependencies/Scripts/Hooks**: Python scripts: `logo/generate.py`, `cip/generate.py`, `icon/generate.py`.
- **Value to `ccba-agent-platform`**: Generates visual interface components and branding elements programmatically.

### 30. `devops`
- **Category**: `infrastructure`
- **Core Purpose**: Manages serverless infrastructure, Docker, GCP pipelines, and Kubernetes.
- **Instruction Summary**: Optimizes Dockerfiles and deploys Helm/K8s configurations.
- **Dependencies/Scripts/Hooks**: Scripts: `cloudflare_deploy.py` and `docker_optimize.py`.
- **Value to `ccba-agent-platform`**: Configures Docker configurations and Helm charts for deploying Spoke instances.

### 31. `docs`
- **Category**: `utilities`
- **Core Purpose**: Initializes and updates project documentation folders.
- **Instruction Summary**: Enforces structural standardizations for architectures and ADRs.
- **Dependencies/Scripts/Hooks**: Workflows under `references/` for initialization and updates.
- **Value to `ccba-agent-platform`**: Syncs codebase updates with the central documentation directory.

### 32. `docs-seeker`
- **Category**: `dev-tools`
- **Core Purpose**: Fetches API documentation files using `llms.txt` configurations from context7.
- **Instruction Summary**: Parses API specifications to resolve syntax queries.
- **Dependencies/Scripts/Hooks**: Node.js scripts: `detect-topic.js`, `fetch-docs.js`, `analyze-llms-txt.js`.
- **Value to `ccba-agent-platform`**: Retrieves API specs for imported packages during code generation.

### 33. `document-skills`
- **Category**: `multimedia`
- **Core Purpose**: Manages programmatic creation, editing, and parsing of Office files (docx, pdf, pptx, xlsx).
- **Instruction Summary**: Implements OOXML packaging, PDF form filling, PowerPoint templating, and Excel macro-recalculation using LibreOffice.
- **Dependencies/Scripts/Hooks**: Scripts: `docx/ooxml/scripts/pack.py`, `pdf/scripts/fill_fillable_fields.py`, `pptx/scripts/html2pptx.js`, `xlsx/recalc.py`.
- **Value to `ccba-agent-platform`**: Key feature for document processing tasks, including invoice parsing and report generation.

### 34. `excalidraw`
- **Category**: `dev-tools`
- **Core Purpose**: Generates Excalidraw diagrams from codebase layout analyses.
- **Instruction Summary**: Maps project directories into visual canvas structures.
- **Dependencies/Scripts/Hooks**: Python script: `references/render_excalidraw.py` (via Playwright).
- **Value to `ccba-agent-platform`**: Renders system interaction charts automatically.

### 35. `find-skills`
- **Category**: `dev-tools`
- **Core Purpose**: Installs and updates agent skill packages from an online directory.
- **Instruction Summary**: Accesses online index records via the `npx skills` command line.
- **Dependencies/Scripts/Hooks**: References `references/domain-routing.md`.
- **Value to `ccba-agent-platform`**: Allows agents to add third-party helper tools to their workspaces.

### 36. `fix`
- **Category**: `utilities`
- **Core Purpose**: Diagnostic pipeline for code errors, test failures, and build issues.
- **Instruction Summary**: Prevents patching symptoms without resolving the underlying root causes.
- **Dependencies/Scripts/Hooks**: References for CI, logs, test, types, and UI error resolution.
- **Value to `ccba-agent-platform`**: Self-healing tool for resolving test failures in custom packages.

### 37. `frontend-design`
- **Category**: `frontend`
- **Core Purpose**: Guidelines for designing custom, accessible frontends.
- **Instruction Summary**: Restricts generic style patterns to optimize layout density and motion.
- **Dependencies/Scripts/Hooks**: References: `anti-slop-rules.md` and `bento-motion-engine.md`.
- **Value to `ccba-agent-platform`**: Guidelines for designing clean user dashboards.

### 38. `frontend-development`
- **Category**: `frontend`
- **Core Purpose**: Architecture rules for building React and TypeScript applications.
- **Instruction Summary**: Recommends lazy loading, query caching, and router states.
- **Dependencies/Scripts/Hooks**: Reference documents for React, TanStack Query, and TanStack Router.
- **Value to `ccba-agent-platform`**: Design guidelines for React interfaces.

### 39. `ghpm`
- **Category**: `utilities`
- **Core Purpose**: Synchronizes agent workspaces with GitHub Issues and Project boards.
- **Instruction Summary**: Automatically structures and posts issues, tasks, and comments.
- **Dependencies/Scripts/Hooks**: Evals: `evals/evals.json`. References: `references/schema-and-taxonomy.md`.
- **Value to `ccba-agent-platform`**: Automates progress reporting directly on GitHub boards.

### 40. `git`
- **Category**: `dev-tools`
- **Core Purpose**: Ensures secure git actions, including split commits and secret scanning.
- **Instruction Summary**: Automates conventional commits and branch management.
- **Dependencies/Scripts/Hooks**: Reference documents for branch cleanliness and commit formats.
- **Value to `ccba-agent-platform`**: Prevents commiting secrets and formats logs cleanly.

### 41. `gkg`
- **Category**: `dev-tools`
- **Core Purpose**: GitLab Knowledge Graph analyzer using AST parsing and graph databases.
- **Instruction Summary**: Explores definitions, cross-references, and code impact maps.
- **Dependencies/Scripts/Hooks**: Runs GKG CLI local client over port `27495`.
- **Value to `ccba-agent-platform`**: Identifies code coupling and simplifies codebase refactoring.

### 42. `google-adk-python`
- **Category**: `ai-ml`
- **Core Purpose**: Guides agent development using the Google Agent Development Kit (ADK) Python SDK.
- **Instruction Summary**: Designs agent topologies and tools for deployment to Vertex AI.
- **Dependencies/Scripts/Hooks**: 7 reference documents on ADK development and evaluations.
- **Value to `ccba-agent-platform`**: Framework for orchestrating Python agents using Gemini models.

### 43. `html-video`
- **Category**: `frontend`
- **Core Purpose**: Generates MP4 video files from HTML, CSS, and JS configurations.
- **Instruction Summary**: Renders video frames using headless Chromium and FFmpeg.
- **Dependencies/Scripts/Hooks**: CLI `html-video`, Playwright, and FFmpeg.
- **Value to `ccba-agent-platform`**: Generates video reports of agent runs for user reviews.

### 44. `journal`
- **Category**: `utilities`
- **Core Purpose**: Formulates engineering log entries for codebase updates and decisions.
- **Instruction Summary**: Writes records into `./docs/journals/` directories.
- **Dependencies/Scripts/Hooks**: Integrates with the `journal-writer` agent and project organization tools.
- **Value to `ccba-agent-platform`**: Maintains history logs of code additions and changes.

### 45. `llms`
- **Category**: `dev-tools`
- **Core Purpose**: Generates `llms.txt` files to catalog project documentation for LLMs.
- **Instruction Summary**: Parses documentation files and extracts titles and summaries.
- **Dependencies/Scripts/Hooks**: Python script: `scripts/generate-llms-txt.py`.
- **Value to `ccba-agent-platform`**: Catalogs platform APIs to speed up code generation tasks.

### 46. `markdown-novel-viewer`
- **Category**: `utilities`
- **Core Purpose**: Runs a local server to view markdown files in a clean interface.
- **Instruction Summary**: Converts markdown text on the fly and renders Mermaid diagrams.
- **Dependencies/Scripts/Hooks**: Node script: `scripts/server.cjs`. Port finder libraries.
- **Value to `ccba-agent-platform`**: Local viewer for agent reports and diagrams.

### 47. `mcp-builder`
- **Category**: `dev-tools`
- **Core Purpose**: Guidelines for implementing and evaluating Model Context Protocol (MCP) servers.
- **Instruction Summary**: Recommends async SDK connections and strict schema validation.
- **Dependencies/Scripts/Hooks**: Python scripts: `scripts/connections.py` and `scripts/evaluation.py`.
- **Value to `ccba-agent-platform`**: Blueprint for implementing custom MCP connectors.

### 48. `media-processing`
- **Category**: `multimedia`
- **Core Purpose**: Batch optimizes video, audio, and image assets using FFmpeg and ImageMagick.
- **Instruction Summary**: Compresses file formats, changes dimensions, and strips metadata.
- **Dependencies/Scripts/Hooks**: Scripts: `scripts/batch_resize.py` and `scripts/video_optimize.py`.
- **Value to `ccba-agent-platform`**: Optimizes image assets for web interfaces.

### 49. `mermaidjs-v11`
- **Category**: `utilities`
- **Core Purpose**: Guides writing syntax-compliant Mermaid.js v11 text-based diagrams.
- **Instruction Summary**: Renders flowcharts, sequence diagrams, and class mappings.
- **Dependencies/Scripts/Hooks**: Mermaid CLI `@mermaid-js/mermaid-cli` (`mmdc`).
- **Value to `ccba-agent-platform`**: Automatically generates system architecture charts.

### 50. `mintlify`
- **Category**: `dev-tools`
- **Core Purpose**: Reference for building and publishing documentation sites via Mintlify.
- **Instruction Summary**: Configures JSON specifications, MDX pages, and API components.
- **Dependencies/Scripts/Hooks**: Mintlify system CLI package.
- **Value to `ccba-agent-platform`**: Syncs codebase markdown docs with user-facing portals.

### 51. `mobile-development`
- **Category**: `frameworks`
- **Core Purpose**: Architectural standards for native and cross-platform mobile apps.
- **Instruction Summary**: Defines budgets for startup speed, memory usage, and frame rates.
- **Dependencies/Scripts/Hooks**: Reference documents on iOS, Android, and mobile debugging.
- **Value to `ccba-agent-platform`**: Reference design for mobile companions.

### 52. `payment-integration`
- **Category**: `backend`
- **Core Purpose**: Integrates payment gateways, including SePay, Stripe, Polar, and Creem.
- **Instruction Summary**: Verifies webhook signatures and handles subscription lifecycles.
- **Dependencies/Scripts/Hooks**: JS scripts: `sepay-webhook-verify.js` and `polar-webhook-verify.js`.
- **Value to `ccba-agent-platform`**: Connects VietQR payments using SePay webhooks.

### 53. `plans-kanban`
- **Category**: `dev-tools`
- **Core Purpose**: Launches the visual plans board dashboard interface.
- **Instruction Summary**: Runs health checks on the UI port before opening a browser.
- **Dependencies/Scripts/Hooks**: Node script: `scripts/open-dashboard.cjs`.
- **Value to `ccba-agent-platform`**: Visual interface for tracking agent milestone progress.

### 54. `preview`
- **Category**: `utilities`
- **Core Purpose**: Renders visual HTML pages and reports for codebase updates.
- **Instruction Summary**: Formulates HTML slides, diff reviews, and recap summaries.
- **Dependencies/Scripts/Hooks**: HTML templates under `templates/` (architecture, slide-deck).
- **Value to `ccba-agent-platform`**: Renders code changes and risk reviews before merging.

### 55. `problem-solving`
- **Category**: `utilities`
- **Core Purpose**: Problem-solving frameworks (Simplification Cascades, Inversion) for debugging.
- **Instruction Summary**: Simplifies complex paths and tests edge cases at scale.
- **Dependencies/Scripts/Hooks**: Reference documents on refactoring strategies.
- **Value to `ccba-agent-platform`**: Enforces KISS principles on complex data flows.

### 56. `project-management`
- **Category**: `utilities`
- **Core Purpose**: Ephemeral task tracking integrated with markdown plan files.
- **Instruction Summary**: Reads plan files, maps them to session tasks, and updates statuses.
- **Dependencies/Scripts/Hooks**: CLI task operations (`TaskCreate`, `TaskUpdate`).
- **Value to `ccba-agent-platform`**: Enforces status synchronization across multiple agent turns.

### 57. `project-organization`
- **Category**: `utilities`
- **Core Purpose**: Standardizes folder layouts and file naming conventions.
- **Instruction Summary**: Restricts directory locations and enforces kebab-case names.
- **Dependencies/Scripts/Hooks**: Reference files on naming and markdown templates.
- **Value to `ccba-agent-platform`**: Enforces structured folder organization for workspaces.

### 58. `react-best-practices`
- **Category**: `frontend`
- **Core Purpose**: Optimization guidelines for React and Next.js applications.
- **Instruction Summary**: Prevents async waterfalls, barrel imports, and rendering lag.
- **Dependencies/Scripts/Hooks**: 45 rule files under `rules/` and compiled `AGENTS.md`.
- **Value to `ccba-agent-platform`**: Minimizes React dashboard bundle sizes.

### 59. `remotion`
- **Category**: `frontend`
- **Core Purpose**: Generates video assets using React code structures via Remotion.
- **Instruction Summary**: Controls timelines, animations, transitions, and audio syncs.
- **Dependencies/Scripts/Hooks**: 30 rule files under `rules/` (animations, charts, audio).
- **Value to `ccba-agent-platform`**: Automates the rendering of video dashboards.

### 60. `repomix`
- **Category**: `dev-tools`
- **Core Purpose**: Bundles codebase contexts into single files for LLMs.
- **Instruction Summary**: Strips comments and counts tokens before running security audits.
- **Dependencies/Scripts/Hooks**: Python script: `repomix_batch.py` and Secretlint.
- **Value to `ccba-agent-platform`**: Formats clean codebase contexts for downstream subagents.

### 61. `research`
- **Category**: `utilities`
- **Core Purpose**: Systematic research methodology for technology assessments.
- **Instruction Summary**: Uses isolated CLI instances to search and generate reports.
- **Dependencies/Scripts/Hooks**: Config settings `skills.research.useGemini` in `.ck.json`.
- **Value to `ccba-agent-platform`**: Blueprint for structural analysis and technology checks.

### 62. `retro`
- **Category**: `utilities`
- **Core Purpose**: Generates sprint engineering retrospectives using git logs.
- **Instruction Summary**: Analyzes commit velocity, hotspot files, and test coverage ratios.
- **Dependencies/Scripts/Hooks**: Runs git log queries and bash parsing scripts.
- **Value to `ccba-agent-platform`**: Data-driven report generator for tracking development progress.

### 63. `review-pr`
- **Category**: `utilities`
- **Core Purpose**: Reviews PR files against code standards and flags AI-slop patterns.
- **Instruction Summary**: Runs duplicate checks, analyzes diffs, and pushes automated fixes.
- **Dependencies/Scripts/Hooks**: GitHub CLI `gh`, git commands. Enforces standard rules.
- **Value to `ccba-agent-platform`**: Automated gate for reviewing developer code submissions.

### 64. `scout`
- **Category**: `dev-tools`
- **Core Purpose**: Explores repositories using parallel subagents.
- **Instruction Summary**: Registers and schedules file search tasks across multiple directories.
- **Dependencies/Scripts/Hooks**: References: `internal-scouting.md` and `external-scouting.md`.
- **Value to `ccba-agent-platform`**: Speeds up codebase scanning in large monorepos.

### 65. `security-scan`
- **Category**: `utilities`
- **Core Purpose**: Scans workspaces for exposed secrets and dependencies.
- **Instruction Summary**: Audits libraries and flags insecure patterns (like SQL injection).
- **Dependencies/Scripts/Hooks**: Runs `npm audit` and `pip audit` checks.
- **Value to `ccba-agent-platform`**: Prevents commiting hardcoded API keys.

### 66. `sequential-thinking`
- **Category**: `utilities`
- **Core Purpose**: Structured, step-by-step thinking loop for resolving complex tasks.
- **Instruction Summary**: Tracks hypotheses and revisions before confirming solutions.
- **Dependencies/Scripts/Hooks**: Scripts: `process-thought.js` and `format-thought.js`.
- **Value to `ccba-agent-platform`**: Logic engine for troubleshooting backend issues.

### 67. `shader`
- **Category**: `frontend`
- **Core Purpose**: Guides writing fragment shaders using GLSL.
- **Instruction Summary**: Explains shape rendering, noise fields, and procedural textures.
- **Dependencies/Scripts/Hooks**: Contains 12 reference files on coordinates and noise.
- **Value to `ccba-agent-platform`**: Low direct applicability. Useful if interactive 3D elements are added to dashboards.

### 68. `ship`
- **Category**: `dev-tools`
- **Core Purpose**: Releases branches, runs tests, and creates PRs.
- **Instruction Summary**: Bumps versions, generates changelogs, and updates documentation.
- **Dependencies/Scripts/Hooks**: References: `ship-workflow.md` and `pr-template.md`.
- **Value to `ccba-agent-platform`**: Enforces strict deployment checks.

### 69. `shopify`
- **Category**: `frameworks`
- **Core Purpose**: Guides Shopify app and extension development using Shopify CLI.
- **Instruction Summary**: Builds admin widgets and routes GraphQL queries.
- **Dependencies/Scripts/Hooks**: Python script: `scripts/shopify_init.py` (with unit tests).
- **Value to `ccba-agent-platform`**: Low direct applicability unless connecting storefront APIs.

### 70. `show-off`
- **Category**: `other`
- **Core Purpose**: Renders workspace showcases using preference settings.
- **Instruction Summary**: Captures HTML views and saves snapshots.
- **Dependencies/Scripts/Hooks**: Scripts: `preferences.js` and `capture-sections.js` (via Puppeteer).
- **Value to `ccba-agent-platform`**: Visual report generator to showcase agent status.

### 71. `skill-creator`
- **Category**: `dev-tools`
- **Core Purpose**: Framework for building and testing custom agent skills.
- **Instruction Summary**: Scaffolds and refines skills using evaluation tasks.
- **Dependencies/Scripts/Hooks**: Python scripts: `init_skill.py`, `package_skill.py`. Grader agents.
- **Value to `ccba-agent-platform`**: Standard tool for bootstrapping new agent skills.

### 72. `stitch`
- **Category**: `frontend`
- **Core Purpose**: Generates layouts using the Google Stitch API.
- **Instruction Summary**: Exports Tailwind HTML code and styling specifications.
- **Dependencies/Scripts/Hooks**: Scripts: `stitch-quota.ts` and `stitch-generate.ts`.
- **Value to `ccba-agent-platform`**: Generates mockup layouts for dashboard frontends.

### 73. `tanstack`
- **Category**: `frameworks`
- **Core Purpose**: Guides development using the TanStack (Start, Form, AI) libraries.
- **Instruction Summary**: Recommends type-safe routing, forms, and streaming endpoints.
- **Dependencies/Scripts/Hooks**: Technical reference documents in the folder.
- **Value to `ccba-agent-platform`**: Blueprint for styling React forms.

### 74. `team`
- **Category**: `dev-tools`
- **Core Purpose**: Orchestrates parallel agent sessions via shared task databases.
- **Instruction Summary**: Manages work assignments and communication channels.
- **Dependencies/Scripts/Hooks**: Integrates with Claude Code task APIs.
- **Value to `ccba-agent-platform`**: Design pattern reference for multi-agent workflows.

### 75. `tech-graph`
- **Category**: `dev-tools`
- **Core Purpose**: Generates SVG diagrams across 8 visual styles.
- **Instruction Summary**: Validates XML tags and compiles SVG paths.
- **Dependencies/Scripts/Hooks**: Script: `validate-svg.sh`. Requires `librsvg` for PNG export.
- **Value to `ccba-agent-platform`**: Renders system interaction maps.

### 76. `test`
- **Category**: `utilities`
- **Core Purpose**: QA testing framework covering unit, integration, and UI tests.
- **Instruction Summary**: Restricts using mock files to hide underlying issues.
- **Dependencies/Scripts/Hooks**: References: `test-execution-workflow.md` and `ui-testing-workflow.md`.
- **Value to `ccba-agent-platform`**: Standardizes testing rules for all platform modules.

### 77. `threejs`
- **Category**: `frontend`
- **Core Purpose**: Guides building 3D web scenes using Three.js APIs.
- **Instruction Summary**: Searches through Three.js example databases.
- **Dependencies/Scripts/Hooks**: Python script: `scripts/search.py`.
- **Value to `ccba-agent-platform`**: Renders complex interactive 3D visualizations in dashboards.

### 78. `ui-styling`
- **Category**: `frontend`
- **Core Purpose**: Styling interfaces using Tailwind CSS and shadcn/ui.
- **Instruction Summary**: Customizes theme properties, density, and animation speeds.
- **Dependencies/Scripts/Hooks**: Reference documents on styling components.
- **Value to `ccba-agent-platform`**: Standardizes frontend styles to prevent CSS bloat.

### 79. `ui-ux-pro-max`
- **Category**: `frontend`
- **Core Purpose**: Design database containing accessibility rules and charts.
- **Instruction Summary**: Audits interfaces for mobile usability and WCAG standards.
- **Dependencies/Scripts/Hooks**: Markdown-based database files.
- **Value to `ccba-agent-platform`**: Audits user interfaces to guarantee high usability.

### 80. `use-mcp`
- **Category**: `dev-tools`
- **Core Purpose**: Executes MCP tools using client wrappers.
- **Instruction Summary**: Runs commands via LLM interfaces or direct scripts.
- **Dependencies/Scripts/Hooks**: TS scripts: `cli.ts` and `mcp-client.ts`.
- **Value to `ccba-agent-platform`**: Connector code for bridging Python and JS MCP servers.

### 81. `vibe`
- **Category**: `dev-tools`
- **Core Purpose**: Orchestrates autonomous development pipelines from task ingest to release.
- **Instruction Summary**: Links tasks (plan, cook, review, test) through approval gates.
- **Dependencies/Scripts/Hooks**: Workflow markdown instructions.
- **Value to `ccba-agent-platform`**: Orchestration model for coding subagents.

### 82. `watzup`
- **Category**: `utilities`
- **Core Purpose**: Generates end-of-session handoff reports using Git logs.
- **Instruction Summary**: Computes task completion rates and compiles next steps.
- **Dependencies/Scripts/Hooks**: Script: `watzup-scan.cjs` and tests `watzup-scan.test.cjs`.
- **Value to `ccba-agent-platform`**: Auto-generates handoff reports to match project rules.

### 83. `web-design-guidelines`
- **Category**: `frontend`
- **Core Purpose**: Reviews UI code against Vercel's Web Interface guidelines.
- **Instruction Summary**: Downloads rules and checks files for formatting errors.
- **Dependencies/Scripts/Hooks**: Requires `WebFetch` tool to read the online rules repository.
- **Value to `ccba-agent-platform`**: CI checklist gate for reviewing web interfaces.

### 84. `web-frameworks`
- **Category**: `frameworks`
- **Core Purpose**: Guides Next.js App Router and Turborepo development.
- **Instruction Summary**: Optimizes rendering and configures Turborepo caching pipelines.
- **Dependencies/Scripts/Hooks**: Python scripts: `nextjs_init.py` and `turborepo_migrate.py`.
- **Value to `ccba-agent-platform`**: Configures monorepo pipeline tooling.

### 85. `web-testing`
- **Category**: `dev-tools`
- **Core Purpose**: Guides testing interfaces using Playwright, Vitest, and k6.
- **Instruction Summary**: Mitigates test flakiness and monitors visual changes.
- **Dependencies/Scripts/Hooks**: Node script: `scripts/init-playwright.js`.
- **Value to `ccba-agent-platform`**: UI test coverage for the platform web portal.

### 86. `worktree`
- **Category**: `dev-tools`
- **Core Purpose**: Manages git worktrees for parallel feature development.
- **Instruction Summary**: Scaffolds branch environments and cleans stale folders.
- **Dependencies/Scripts/Hooks**: JS CLI wrapper: `scripts/worktree.cjs` and tests.
- **Value to `ccba-agent-platform`**: Prevents concurrent file lock conflicts on Windows.

### 87. `port-evaluator` (formerly `xia`)
- **Category**: `dev-tools`
- **Core Purpose**: Code adaptation tool for porting features from external projects.
- **Instruction Summary**: Analyzes code structures and port targets safely.
- **Dependencies/Scripts/Hooks**: Integrates with `/ck:repomix` and `/ck:scout`.
- **Value to `ccba-agent-platform`**: Clean model for porting external database packages.

---

## Part 4: Recommendations for `ccba-agent-platform`

To improve developer productivity, maintain code quality, and optimize AI utilization, the following structural enhancements should be applied to `ccba-agent-platform`:

### 1. Unified Event-Driven Hook System
- **Action**: Implement a local shell wrapper or pre-command hook loader in `packages/ccba-agent` that mirrors the ClaudeKit JSON hook lifecycle.
- **Goal**: Intercept critical developer actions (e.g. initiating a Spoke deployment, importing an untested third-party package) before running them on the host. This prevents data loss (via `accidental-data-loss-prevention`) and enforces credentials checks.
- **Implementation**: Write a Node or Python middleware that reads `settings.json` equivalent constraints and runs validation checks on standard streams.

### 2. File-Based State Persistence and Recovery
- **Action**: Adapt the `latest.md` and `plan.md` patterns to save agent session logs.
- **Goal**: LLM context compactions or session crashes lose temporary memory. Storing state in Markdown tables and phase files inside the `.agents/` folder ensures subsequent runs can resume without losing context.
- **Implementation**: Build a deterministic state reconciler CLI tool (similar to `ck plan`) to transition task checkboxes safely without corrupting layouts.

### 3. Integrated Document Skills (`document-skills`)
- **Action**: Reuse the OOXML and LibreOffice macro wrappers (`xlsx/recalc.py`, `pdf/fill_fillable_fields.py`) from the ClaudeKit skills directory.
- **Goal**: Simplify processing Vietnamese legal documents, filling PDF templates, and exporting Excel reports.
- **Implementation**: Wrap these helper scripts inside the platform's `ccba-pdf-prep` or custom OCR packages to replace redundant implementations.

### 4. Custom MCP Server for Platform Capabilities
- **Action**: Bundle local database utilities and legal text search tools into a structured, async MCP server.
- **Goal**: Expose custom platform endpoints (like Vietnamese law indexes or AI Gateway status) to all active subagents in a token-efficient manner.
- **Implementation**: Follow the strict schema validation and error boundaries described in `mcp-builder` to prevent servers from hanging.

### 5. Multi-Agent Team Coordination
- **Action**: Adopt the shared-task model (`TaskList` and `SendMessage` APIs) to orchestrate multi-agent runs on the platform.
- **Goal**: Enable independent subagent sessions to collaborate on complex milestones (like generating slides, checking security audits, and shipping code) in parallel.
- **Implementation**: Implement a file-based task log database that agents read and update concurrently, using worktrees (`worktree`) to avoid file locks.
