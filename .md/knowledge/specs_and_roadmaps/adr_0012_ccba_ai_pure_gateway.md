# ADR 0012: Chuẩn Hóa `ccba-ai` thành Pure AI Gateway SDK

**Trạng thái:** Accepted
**Ngày:** 2026-08-14
**Tác giả:** AI Agent (Antigravity / Claude Sonnet 4.6)

---

## Bối Cảnh

`packages/ccba-ai` được định vị là Pure AI Gateway SDK kết nối LiteLLM Server Spark
(`:8090`, Tailscale `100.83.192.30`, 22 models). Tuy nhiên sau đợt quét kiến trúc
(ADR 0011 → Architecture Scan Report), package có một số vấn đề kỹ thuật cần xử lý.

---

## Vấn Đề Được Xác Định (Đã Kiểm Chứng Từ Code Thực Tế)

### 1. I/O Stream Reconfigure Top-Level (Vi phạm Pattern P2.2)

```python
# TRƯỚC — top-level module scope (mcp_server.py dòng 15-20)
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")
```

Khi bất kỳ code nào `import ccba_ai.mcp_server`, đoạn này chạy ngay lập tức, phá vỡ
Pytest stream capture và tiềm ẩn rủi ro khi dùng như một module thư viện.

### 2. Hardcoded Absolute Paths trong `legal_knowledge.py`

```python
SPOKE_LOCAL_PATH = Path("D:/GitHubProjects/ccba-legal-knowledge/legal_docs")
SPOKE_REGISTRY_PATH = Path("D:/GitHubProjects/ccba-legal-knowledge/legal_registry.yaml")
```

Hai constants này hardcode đường dẫn máy cá nhân, làm vỡ CI/CD và máy khác trong team.

### 3. Dead Export `legal_knowledge`

Qua `grep` toàn bộ codebase: `legal_knowledge` singleton có **0 caller** bên ngoài
`__init__.py` của chính nó. Export này tồn tại từ ticket thiết kế nhưng chưa bao giờ
được sử dụng thực tế.

### 4. Docstrings Không Đầy Đủ trong `client.py`

Các public methods `chat()`, `stream()`, `models()`, `transcribe()` của cả `AIClient`
và `AsyncAIClient` thiếu `Args:`, `Returns:`, `Raises:` sections chuẩn Google style.

---

## Quyết Định

### ✅ Thực hiện

1. **Di chuyển I/O reconfigure vào `_configure_utf8_streams()` → chỉ gọi trong `main()`**
   — bảo vệ module khỏi side-effect khi bị import.

2. **Xóa `SPOKE_LOCAL_PATH` và `SPOKE_REGISTRY_PATH` hardcoded**
   — thay bằng dynamic resolution hoàn toàn qua env vars:
   - `CCBA_KNOWLEDGE_SPOKE_PATH` → spoke document directory
   - `CCBA_KNOWLEDGE_REGISTRY_PATH` → spoke registry YAML path

3. **Annotate `legal_knowledge` là dead export** trong `__init__.__all__`
   với comment rõ ràng, giữ cho API stability nhưng không khuyến khích dùng.

4. **Bổ sung Google-style docstrings** cho toàn bộ public methods của `AIClient`
   và `AsyncAIClient`.

### ❌ Không thực hiện (đã bác bỏ sau Adversarial Review)

- **Không di chuyển `AuditFinding`, `AuditReport`, `protocols.py`**: Đây là shared
  Pydantic types phục vụ giao tiếp giữa AI Gateway và các QC skills. Không có package
  domain nào phù hợp hơn; di chuyển sẽ tạo dependency cycle.
- **Không thao túng `__all__`** để "ẩn" domain exports: Không có caller nào dùng
  wildcard `from ccba_ai import *`; thao túng `__all__` không có tác dụng thực tế.
- **Không di chuyển `services/seo.py`**: SEO Auditor được consume bởi
  `scripts/validation/seo_audit.py` và test suite, không gây domain pollution thực chất.

---

## Hệ Quả

| Khía cạnh | Trước | Sau |
|---|---|---|
| I/O Safety khi import | ❌ Side-effect top-level | ✅ Entrypoint guard |
| Portable paths | ❌ Hardcoded `D:/...` | ✅ Env var + relative hub |
| Dead exports | Không được chú thích | ✅ Annotated với NOTE |
| Docstring coverage | Thiếu Args/Returns | ✅ Google style đầy đủ |
| Backward compat | N/A | ✅ 45/45 tests PASSED |

---

## Tài Liệu Liên Quan

- [ADR 0011](adr_0011_legal_intel_deep_module.md) — Deep Seam cho ccba-legal-intel
- [AGENTS.md](../../../.agents/AGENTS.md) — Layer 1 Constitution
- [session_learnings.md — Trụ Cột 2 (P2.2)](../session_learnings.md) — Top-level side-effect anti-pattern
