# CCBA Naming Conventions

> Quy ước đặt tên file, folder, và artifacts trong hệ thống CCBA.

## Files

### Seminar Materials
```
CCBA_RD_SEMINAR_NNN_RevXX-DD.MM.YY-Title.{ext}
```
| Phần | Ý nghĩa | Ví dụ |
|------|---------|-------|
| `CCBA_RD_SEMINAR_` | Prefix cố định | — |
| `NNN` | Số thứ tự 3 chữ số | 001, 002, 003 |
| `RevXX` | Revision | Rev00, Rev01 |
| `DD.MM.YY` | Ngày seminar | 21.03.26 |
| `Title` | Tên chủ đề (kebab-case) | Lite-On-MOC_DOC_Inspections |
| `{ext}` | pdf, pptx, md, docx | — |

### VBPL Documents (do CCBA tổng hợp)
```
CCBA_RD_VBPL_NNN_RevXX-ShortName.{ext}
```
Ví dụ: `CCBA_RD_VBPL_003_Rev00-ND_06_2021.docx`

### AI Agent Outputs
- Skills: `lowercase_with_underscores` (folder + file names)
- Workflows: `kebab-case.md`
- YAML data: `lowercase_with_underscores.yaml`
- Templates: `lowercase_with_underscores.md`

## Folders

### Hub (ccba-agent-platform)
```
.agent/skills/{skill-name}/     ← kebab-case
.agent/workflows/               ← files: kebab-case.md
knowledge/                      ← files: snake_case.md
rules/                          ← files: snake_case.md
scripts/                        ← files: snake_case.py
templates/                      ← files: snake_case.{ext}
tools/                          ← files: snake_case
.md/                            ← processing workspace (temp)
```

### Spoke (Project folder)
```
.md/                            ← workspace_context.yaml + local config
[output files]                  ← theo naming convention tương ứng
```

### OneDrive Source Data
```
BIM_VBPL/
  YYYY/                         ← Năm
    CCBA_RD_SEMINAR_NNN_*       ← Seminar materials
    Dự thảo NĐQLCL2026.../     ← Draft VBPL folders
    BXD_*.pdf                   ← Official VBPL downloads
```

## Git Conventions

### Branch naming
```
feature/{short-description}
fix/{short-description}
```

### Commit messages
```
feat: add legal-document-tracker skill
fix: update checklist items per NĐ 35/2023
docs: update session_learnings for 2026-03-28
chore: gitignore .md/ temp files
```
