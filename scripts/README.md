# CCBA Scripts Infrastructure & Domain Architecture

Tài liệu hướng dẫn cấu trúc và nguyên tắc phân tầng thư mục `scripts/` thuộc CCBA Agent Platform.

---

## 🏛️ Kiến trúc 2 Tầng (2-Tier Architecture)

Thư mục `scripts/` áp dụng mô hình 2 tầng để vừa duy trì giao diện gọi CLI ngắn gọn cho Agent/Workflows, vừa giữ cấu trúc phân nhóm domain ngăn nắp:

```
scripts/
├── [Root CLI Entry-Points & Bridge Adapters]
│   ├── run_harness_evals.py     ──> calls scripts.eval.run_harness_evals.main()
│   ├── run_isolated_tests.py    ──> calls scripts.eval.run_isolated_tests.main()
│   ├── legal_sync.py            ──> calls scripts.legal.legal_sync.main()
│   ├── audit_pr_comments.py     ──> calls scripts.validation.audit_pr_comments.main()
│   ├── compile_knowledge.py     ──> calls scripts.spoke.compile_knowledge.main()
│   ├── log_eval_miner.py        ──> calls scripts.eval.log_eval_miner.main()
│   └── update_arch_stats.py     ──> calls scripts.security.update_arch_stats.main()
│
├── [Domain Implementation Subfolders]
│   ├── eval/            — Harness CI gates, sandbox wrapper, isolated tests, process_safety
│   ├── legal/           — Legal intelligence & notebooklm sync engines
│   ├── security/        — Maskara rules, security stats, credentials scanner
│   ├── spoke/           — Spoke synchronization & knowledge compilation
│   ├── validation/      — PR comment auditing & governance gates
│   ├── hooks/           — Git pre-commit & session lifecycle hooks
│   └── templates/       — Code & document generation templates
│
└── [Deep Utilities & Thin Adapters]
    ├── maskara.py       — Deep Module: Secret detection & redaction engine
    ├── doc_auditor.py   — Deep Module: Governance & document validation engine
    ├── validate_docs.py ──> Thin adapter bọc DocumentAuditor
    └── validate_skills.py─> Thin adapter bọc DocumentAuditor
```

---

## 📜 Nguyên tắc Vận hành (Rules & Conventions)

1. **Root Bridge Adapters**: Tất cả các lệnh terminal gọi từ Agent, Workflows, hoặc CI (`python scripts/<script_name>.py`) đều thông qua tệp Bridge Adapter ở root. Tuyệt đối không gọi trực tiếp vào subfolders để đảm bảo tính tương thích ngược 100%.
2. **KISS & Locality**: Logic triển khai chính nằm trong domain subfolder tương ứng hoặc Deep Module. Tệp adapter tại root duy trì tối giản (~7 dòng code) chỉ làm nhiệm vụ `sys.exit(main())`.
3. **Process Safety**: Mọi script thực thi tiến trình ngầm bắt buộc phải sử dụng tiện ích từ `scripts.eval.process_safety` (`ensure_single_instance`, `kill_process_tree`, `get_venv_python`).
