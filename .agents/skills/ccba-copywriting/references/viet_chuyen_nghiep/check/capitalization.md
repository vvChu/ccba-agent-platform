# Viết Hoa & Tiêu Đề — Capitalization

**Module:** check/capitalization
**Mục đích:** Quy tắc viết hoa và phân cấp tiêu đề trong tiếng Việt.

---

## 1. Viết hoa — Không Title Case

Tiếng Việt CHỈ viết hoa chữ cái đầu tiên, KHÔNG viết hoa mỗi từ.

```
✅ Chủ tịch nước          ❌ Chủ Tịch Nước
✅ Bộ trưởng Bộ Giáo dục  ❌ Bộ Trưởng Bộ Giáo Dục
✅ Hướng dẫn sử dụng      ❌ Hướng Dẫn Sử Dụng
```

**Viết hoa khi:**
- Tên riêng người: Nguyễn Văn An
- Địa danh: Hà Nội, sông Hồng (❌ Sông Hồng — "sông" là danh từ chung)
- Chức danh kèm tổ chức: Bộ trưởng Bộ Giáo dục
- Sau dấu hai chấm trích dẫn: Ông ta nói: "Đây là..."

---

## 2. Tiêu đề

### Phân cấp

**H1 — Hai style:**
- **Sách/tài liệu:** `# 3.1 Thiết kế Knowledge & Workspace`
- **Blog/article:** `# TIÊU ĐỀ IN HOA` hoặc `# Tiêu đề viết hoa chữ đầu`

**H2+ — LUÔN:** Chỉ viết hoa chữ cái đầu tiên

### Không dùng dấu hai chấm trong tiêu đề

```
❌ Vibe coding: lỗi không phải ở AI
✅ Vibe coding - Lỗi không phải ở AI
✅ Vấn đề của vibe coding không phải ở AI
```

---

## Grep Patterns

| Pattern | Search | Quy tắc |
|---------|--------|---------|
| Title Case heading | `^##? [A-ZÀÁẢÃẠ].*[A-ZÀÁẢÃẠ]` | Nghi Title Case — kiểm tra |
| Colon in heading | `^#.*: ` | Cấm dấu hai chấm trong tiêu đề |

---

## Checklist hoàn thành

- [ ] Viết hoa: chỉ chữ đầu tiên (không Title Case)
- [ ] Tiêu đề: không dùng dấu hai chấm
- [ ] Tiêu đề H2+: chỉ viết hoa chữ đầu
