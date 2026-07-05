# Project: TVPL Crawler Upgrade (Run 4)

## Architecture
- `ccba-legal-intel` is a Python package handling legal intelligence (parsing, crawling, amendments).
- TVPL crawler (`ccba_legal/crawler.py`) interacts with TVPL website using Chrome DevTools Protocol (CDP) or similar mechanisms to extract metadata and PDF documents.

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| 1 | TVPL Crawler Upgrade | Implement R1 (three-tier cache), R2 (synonym mapping injection), R3 (VIP session lock) | None | IN_PROGRESS |

## Interface Contracts
- TVPL Crawler API: `ccba_legal/crawler.py` should expose appropriate metadata extraction and downloading APIs.
- Synonyms resource: `.agents/skills/ccba-legal-intel/resources/relation_synonyms.yaml` dynamic loading.
- Mutex lock: `.md/data/tvpl_vip_session.lock`.

## Code Layout
- Package: `packages/ccba-legal-intel/ccba_legal`
- Tests: `packages/ccba-legal-intel/tests`
- Synonyms: `.agents/skills/ccba-legal-intel/resources/relation_synonyms.yaml`
