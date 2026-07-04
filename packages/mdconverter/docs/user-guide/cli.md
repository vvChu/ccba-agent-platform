# CLI Commands

Complete reference for all mdconvert commands.

## convert

Convert documents to Markdown.

```bash
mdconvert convert INPUT [OPTIONS]
```

### Arguments

| Argument | Description |
|----------|-------------|
| `INPUT` | Input file or directory to convert |

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `-o, --output` | Output directory | Same as input |
| `-r, --recursive` | Recursively process directories | False |
| `-t, --tool` | Conversion tool: auto, gemini, pandoc, llamaparse | auto |
| `--dry-run` | Show what would be converted | False |

### Examples

```bash
# Convert single file
mdconvert convert document.pdf

# Convert directory recursively
mdconvert convert ./docs/ -r -o ./output/

# Use specific tool
mdconvert convert scan.pdf --tool llamaparse

# Dry run
mdconvert convert ./docs/ --dry-run
```

---

## validate

Validate Markdown files for quality and structure.

```bash
mdconvert validate TARGET [OPTIONS]
```

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `-f, --fix` | Automatically fix issues | False |

### Examples

```bash
# Validate a file
mdconvert validate document.md

# Validate and fix a directory
mdconvert validate ./output/ --fix
```

---

## lint

Lint Markdown files using VN Legal rules.

```bash
mdconvert lint [TARGET] [OPTIONS]
```

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `-f, --fix` | Automatically fix lint issues | False |
| `--vn-only` | Only run Vietnamese legal checks | False |

### VN Legal Rules

| Rule | Description |
|------|-------------|
| VN001 | Merged list items (a, b, c on same line) |
| VN002 | Suspicious numbering reset |
| VN003 | Missing blank line before Điều headers |
| VN004 | Incorrect Điểm format |

---

## config

Show current configuration.

```bash
mdconvert config
```

### Output

Displays a table with all current settings including proxy URL, models, tokens, and thresholds.

---

## CCBA Platform Utility CLIs

Additional agent platform tools implemented in the `scripts/` directory:

### hook_runner

Unified Hook Runner for session lifecycle hooks (session-init, pre-tool, post-tool).

```bash
python scripts/hook_runner.py EVENT [OPTIONS]
```
- **EVENT**: `session-init`, `pre-tool`, `post-tool`
- **Options**: `--tool <name>`, `--path <path>`, `--args <json_args>`

---

### plan_manager

Managed Implementation Plan Builder and Status Checker.

```bash
python scripts/plan_manager.py [create|check|status] [OPTIONS]
```
- **create**: `--title "<title>" --phases "<phase1,phase2>"`
- **check**: `--plan <path> --phase <id> --status <pending|in-progress|completed>`
- **status**: `--plan <path>`

---

### team_coordinator

Multi-Agent Task Sharing Coordinator.

```bash
python scripts/team_coordinator.py [list|add|claim|complete] [OPTIONS]
```
- **list**: Show all tasks and statuses
- **add**: `--name "<name>" [--owner "<agent>"]`
- **claim**: `--name "<name>" --owner "<agent>"`
- **complete**: `--name "<name>"`

---

### find_skills

Interactive Search CLI for ClaudeKit and Marketing skills.

```bash
python scripts/find_skills.py [query]
```

---

### seo_audit

Technical SEO Compliance Auditor for HTML and Markdown files.

```bash
python scripts/seo_audit.py FILE_PATH
```

---

### ccba-mcp

Custom Model Context Protocol JSON-RPC Server.

```bash
# Start the MCP server locally over stdin/stdout
python -m ccba_ai.mcp_server
```
