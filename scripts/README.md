# CCBA Scripts Infrastructure & Domain Architecture

Tài liệu hướng dẫn cấu trúc và nguyên tắc phân tầng thư mục `scripts/` thuộc CCBA Agent Platform.

---

## 🏛️ Kiến trúc Phân Tầng (Domain Clustered Architecture)

Tất cả console scripts được đăng ký **trực tiếp** vào subdirectory targets qua `pyproject.toml`
— không còn forwarding stub ở root để tránh gây nhiễu khi AI Agent tìm kiếm code.

```
scripts/
├── [Deep Utilities — Standalone Modules]
│   ├── doc_auditor.py    — Deep Module: Governance & document validation engine
│   ├── maskara.py        — Deep Module: Secret detection & redaction engine
│   ├── safe_pytest.py    — CLI wrapper: Scoped pytest execution
│   ├── safe_runner.py    — CLI wrapper: Detached process runner
│   ├── sync_spoke.py     — CLI entrypoint: Spoke synchronization
│   ├── validate_docs.py  — Thin adapter wrapping DocumentAuditor
│   ├── validate_skills.py— Thin adapter wrapping DocumentAuditor
│   └── legal_sync.py     — Thin adapter (re-exports ccba_legal.sync symbols)
│
├── [Domain Implementation Subfolders]
│   ├── eval/             — Harness CI gates, sandbox wrapper, isolated tests
│   ├── legal/            — Legal intelligence & notebooklm sync engines
│   ├── security/         — Maskara rules, security stats, credentials scanner
│   ├── spoke/            — Spoke synchronization & knowledge compilation
│   ├── validation/       — PR comment auditing & governance gates
│   ├── hooks/            — Git pre-commit & session lifecycle hooks
│   └── templates/        — Code & document generation templates
```

### Console Scripts (`pyproject.toml` → direct subdirectory targets)

| Command | Target |
|---|---|
| `ccba-eval` | `scripts.eval.run_harness_evals:main` |
| `ccba-test` | `scripts.eval.run_isolated_tests:main` |
| `ccba-audit-pr` | `scripts.validation.audit_pr_comments:main` |
| `ccba-compile-knowledge` | `scripts.spoke.compile_knowledge:main` |
| `ccba-legal-sync` | `scripts.legal.legal_sync:main` |
| `ccba-seo-audit` | `scripts.validation.seo_audit:main` |

---

## 📜 Nguyên tắc Vận hành (Rules & Conventions)

1. **No Root Stubs**: Tuyệt đối không tạo forwarding stub ở root `scripts/`. Thay vào đó, đăng ký console script trực tiếp trong `pyproject.toml` trỏ vào subdirectory module.
2. **KISS & Locality**: Logic triển khai chính nằm trong domain subfolder tương ứng hoặc Deep Module. Root chỉ chứa Standalone Deep Modules và Thin Adapters có lý do rõ ràng.
3. **Process Safety**: Mọi script thực thi tiến trình ngầm bắt buộc phải sử dụng tiện ích từ `scripts.eval.process_safety` (`ensure_single_instance`, `kill_process_tree`, `get_venv_python`).
