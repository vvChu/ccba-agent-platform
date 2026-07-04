# Quick Start

Get started with mdconvert in 5 minutes.

## Basic Usage

### Convert a Single File

```bash
mdconvert convert document.pdf
```

This creates `document.md` in the same directory.

### Convert a Directory

```bash
mdconvert convert ./documents/ --recursive
```

### Specify Output Directory

```bash
mdconvert convert document.pdf --output ./markdown/
```

### Choose Conversion Tool

```bash
# Use Pandoc (best for DOCX)
mdconvert convert document.docx --tool pandoc

# Use Gemini (best for PDFs with images)
mdconvert convert document.pdf --tool gemini

# Use LlamaParse (best for scanned PDFs)
mdconvert convert scanned.pdf --tool llamaparse
```

## Performance Options (v2.0)

### Enable Caching

Skip unchanged files on re-runs:

```bash
mdconvert convert ./documents/ --cache
```

### Verbose / Quiet Output

```bash
# Debug output
mdconvert convert document.pdf --verbose

# Minimal output (warnings and errors only)
mdconvert convert document.pdf --quiet
```

## Validate & Lint

### Validate Markdown Quality

```bash
mdconvert validate ./output/
```

### Lint with Auto-Fix

```bash
mdconvert lint ./output/ --fix
```

### Vietnamese Legal Document Check

```bash
mdconvert lint ./legal-docs/ --vn-only
```

## View Configuration

```bash
mdconvert config
```

Output:

```text
┏━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Setting              ┃ Value                        ┃
┡━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ Proxy URL            │ http://127.0.0.1:8045        │
│ Models               │ gemini-3-flash, ...          │
│ Max Tokens           │ 65536                        │
└──────────────────────┴──────────────────────────────┘

```
