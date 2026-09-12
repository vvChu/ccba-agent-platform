# Checklist-Based Review Workflow

How to apply structured review checklists during code review.

## When to Use

- Pre-landing review (from shipping / release pipeline)
- Explicit request for checklist review
- Security audit before release
- Review subagents when evaluating significant changes (10+ files or security-sensitive)

## Workflow

### 1. Auto-Detect Project Type

Check repository markers using cross-platform / PowerShell commands:

```powershell
# Check for Python monorepo stack
if (Test-Path "pyproject.toml") { "python" }

# Check for web app frameworks
if (Test-Path "package.json") {
    $pkg = Get-Content "package.json" -Raw -Encoding UTF8
    if ($pkg -match '"(react|vue|svelte|next|nuxt|angular)"') { "web-app" }
}

# Check for API patterns
$apiDirs = @("src/routes", "src/api", "src/controllers", "app/controllers")
if ($apiDirs | Where-Object { Test-Path $_ }) { "api" }
```

Cross-platform shell equivalent:
```bash
# Check for Python stack
[ -f "pyproject.toml" ] && echo "python"

# Check for web app frameworks (Cross-platform git grep)
if [ -f "package.json" ] && git grep -qiE '"(react|vue|svelte|next|nuxt|angular)"' -- package.json; then
    echo "web-app"
fi

# Check for API patterns
for d in src/routes src/api src/controllers app/controllers; do
    if [ -d "$d" ]; then
        echo "api"
        break
    fi
done
```

### 2. Load Checklists

Always load: `checklists/base.md`

Overlay based on detection:
- `python` → also load `checklists/python.md` (ADR-0035, mypy strict, Windows utf-8 encoding, KISS)
- `web-app` → also load `checklists/web-app.md`
- `api` → also load `checklists/api.md`
- Multiple detected → load all matching overlays

### 3. Get the Diff

```bash
git fetch origin main --quiet
git diff origin/main
```

**CRITICAL:** Read the FULL diff before flagging anything. Checklist suppressions require full context.

### 4. Two-Pass Review

**Pass 1 (CRITICAL) — Run first:**
- Scan diff against ALL critical categories (base + overlays)
- Each finding must include: `[file:line]`, problem, fix
- These block the landing/release pipeline

**Pass 2 (INFORMATIONAL) — Run second:**
- Scan diff against ALL informational categories (base + overlays)
- Same format: `[file:line]`, problem, fix
- Included in PR body but don't block

### 5. Check Suppressions

Before reporting any finding, verify it's NOT in the suppressions list (bottom of `base.md`).

Key suppressions:
- Already addressed in the diff
- Readability-aiding redundancy
- Style/formatting issues
- "Consider using X" when Y works fine

### 6. Output

```
Pre-Landing Review: N issues (X critical, Y informational)

**CRITICAL** (blocking):
- [packages/ccba-core/src/service.py:42] Direct private import from `ccba_pkg._internal` violates ADR-0035
  Fix: Import public seam through `ccba_pkg` or export symbol via `__all__`

**Issues** (non-blocking):
- [packages/ccba-core/src/utils.py:88] Missing Google-style docstring on public function
  Fix: Add function docstring describing parameters and return type
```

### 7. Critical Issue Resolution

For each critical issue, use `ask_question`:
- Problem with `file:line`
- Recommended fix
- Options:
  - A) Fix now (recommended)
  - B) Acknowledge and proceed
  - C) False positive — skip

If user chose A (fix): apply fixes, commit, then re-run tests before continuing.

## Integration with Shipping Pipeline

The release pipeline calls this workflow before landing changes. Critical findings block the pipeline. Informational findings are included in the PR body.

## Integration with /ccba-code-review

When invoked as part of standard code review, the checklist augments (not replaces) the existing scout → review → fix → verify pipeline. Checklist findings are merged with the review subagents' findings.
