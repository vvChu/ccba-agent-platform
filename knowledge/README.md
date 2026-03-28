# Knowledge Base — CCBA Hub

> Đây là thư mục chứa **kiến thức tích lũy** từ tất cả phiên làm việc.
> Được tập trung tại Hub theo kiến trúc Hub-and-Spoke (2026-03-28).

## Files

| File | Mô tả | Cập nhật bởi |
|------|--------|-------------|
| `session_learnings.md` | Patterns, Anti-patterns, Solutions tích lũy | `/session-retrospective` workflow |

## Kiến trúc

```
ccba-agent-platform (HUB)
├── knowledge/          ← BẠN ĐANG Ở ĐÂY
│   └── session_learnings.md
├── .agent/skills/      ← Tất cả skills
├── .agent/workflows/   ← Tất cả workflows
└── .md/                ← Processing workspace

Các workspace khác (SPOKES)
├── .md/workspace_context.yaml  ← Chỉ local config
└── [output files]              ← Kết quả xử lý cuối cùng
```

## Nguyên tắc

1. **Knowledge chung** → lưu ở đây (Hub)
2. **Context riêng workspace** → lưu ở `.md/` của workspace đó (Spoke)
3. **Output cuối cùng** → lưu ở thư mục đích tương ứng
4. **Temp/processing files** → lưu ở `.md/` của Hub (gitignored)
