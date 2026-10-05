---
request_id: req-20261005-pr3-code
from_agent: antigravity
to_agent: grok
request_type: implement
subject: 'Implement PR-3: Declarative Package Bindings & Dynamic Package Discovery'
timestamp: '2026-10-05T14:34:00+07:00'
source_documents:
  - scripts/tests/test_declarative_package_bindings.py
  - .agents/skills/platform-loader/catalog_base.yaml
  - scripts/governance/compile_catalog.py
  - scripts/spoke/spoke_bootstrap.py
  - scripts/spoke/sync/sdk_inspector.py
output_path: .md/peer_exchange/grok_code_pr3_package_bindings.md
context: Triển khai mã nguồn cho PR-3 (Action Item 2) để bộ test TDD `scripts/tests/test_declarative_package_bindings.py` chuyển từ ĐỎ sang XANH 100%, sau đó recompile catalog.
---

# YÊU CẦU TRIỂN KHAI MÃ NGUỒN (TDD IMPLEMENTATION)
## PR-3: DECLARATIVE PACKAGE BINDINGS & DYNAMIC DISCOVERY (ADR-0062)

> **Gửi tới**: Grok (Fast Coding Worker — `grok-4.7-build-fast`)  
> **Từ**: Antigravity (Lead Architect & Orchestrator)  
> **Nhiệm vụ**: Triển khai chính xác các thay đổi cho 4 tệp mục tiêu và chạy `compile_catalog.py --write` để bộ test TDD `scripts/tests/test_declarative_package_bindings.py` đạt **5/5 PASS**, không gây hồi quy các test cũ.

---

### 1. Hợp Đồng Kiểm Thử Bắt Buộc (Test Contract)

Antigravity đã viết sẵn bộ test TDD tại [`scripts/tests/test_declarative_package_bindings.py`](file:///home/vvc/ccba/ccba-agent-platform/scripts/tests/test_declarative_package_bindings.py). Cần đáp ứng:

1. **`.agents/skills/platform-loader/catalog_base.yaml`**:
   - Khai báo khóa `package_bindings:` ở cuối file:
   ```yaml
   package_bindings:
     schema_version: 1
     tier0:
       - ccba-harness
       - ccba-ai
     archetypes:
       knowledge_corpus:
         - name: ccba-legal-intel
           when: legal_related
       project_delivery:
         - ccba-qc-core
         - ccba-ooxml
         - ccba-pdf-prep
         - mdconverter
       enterprise_governance:
         - ccba-ooxml
         - ccba-pdf-prep
         - mdconverter
     bundles:
       _bim:
         - ccba-diagram
     categories:
       - name: AI Gateway SDKs
         packages: [ccba-harness, ccba-ai]
       - name: Engineering QC SDKs
         packages: [ccba-qc-core]
       - name: Office & Document Processing SDKs
         packages: [ccba-ooxml, ccba-pdf-prep, mdconverter]
       - name: Legal Intelligence SDKs
         packages: [ccba-legal-intel]
       - name: Diagram SDKs
         packages: [ccba-diagram]
       - name: Extension SDKs
         packages: [ccba-notebooklm, ccba-maskara]
   ```

2. **`scripts/governance/compile_catalog.py`**:
   - Thêm `compile_package_bindings(hub_root: Path, base_data: dict[str, Any]) -> dict[str, Any]`:
     - Kiểm tra `tier0` phải chứa `ccba-harness` và `ccba-ai`.
     - Kiểm tra mọi package name: folder `packages/<name>/pyproject.toml` phải tồn tại. Nếu không tồn tại: raise `CatalogCompileError(f"package '{pkg_name}' pyproject.toml missing")`.
     - Trả về dict bindings đã chuẩn hóa.
   - Bổ sung `"package_bindings"` vào `_BASE_FIELDS`:
     ```python
     _BASE_FIELDS: tuple[str, ...] = (
         "hub_path",
         "hub_repo",
         "notebook_ids",
         "bundles",
         "rules",
         "knowledge",
         "guardrails",
         "package_bindings",
     )
     ```
   - Trong `compile_catalog_dict`: gọi `compile_package_bindings` và gán `"package_bindings": package_bindings`.

3. **`scripts/spoke/spoke_bootstrap.py`**:
   - Triển khai hàm `resolve_install_set(hub_root: Path, *, archetype: str, project_type: str, additional_bundles: Sequence[str] = (), declared_packages: Sequence[str] = (), legal_related: bool = False) -> list[str] | None`:
     - Đọc `catalog.yaml` từ `hub_root`. Nếu không có `package_bindings`, trả về `None` (caller giữ fallback cũ).
     - Nếu có:
       * Gom tier0 packages.
       * Nếu `declared_packages` có giá trị: thêm vào.
       * Nếu `declared_packages` rỗng:
         + Lấy packages theo `archetype` (lọc theo `when: legal_related` nếu có).
         + Lấy các bundles tương ứng với `project_type` từ `catalog["bundles"]` cộng `additional_bundles`, sau đó tra cứu trong `package_bindings["bundles"]` để gom các bundle-specific packages (ví dụ: `_bim` -> `ccba-diagram`).
       * Sắp xếp kết quả trả về theo `discover_package_topology(hub_root)`.
   - Trong `SpokeBootstrap.resolve_target_packages`:
     - Gọi `resolve_install_set(...)`. Nếu kết quả không phải `None`, trả về kết quả đó. Nếu là `None`, giữ logic fallback hiện tại.

4. **`scripts/spoke/sync/sdk_inspector.py`**:
   - Trong `SharedSdkInspector.resolve_packages_to_check`:
     - Gọi `resolve_install_set(...)`. Nếu không phải `None`, trả về danh sách đó; nếu `None`, giữ logic fallback cũ.
   - Trong `SharedSdkInspector.get_categorized_recommendations`:
     - Đọc `categories` từ `catalog.get("package_bindings", {}).get("categories")` nếu có, thay cho dict cứng (nhưng vẫn fallback về dict cũ nếu catalog không có).

5. **Recompile catalog**:
   - Chạy `python scripts/governance/compile_catalog.py --write` để cập nhật `catalog.yaml`.
   - Đảm bảo `python scripts/governance/compile_catalog.py --check` trả về in-sync.

---

### 2. Định Dạng Kết Quả

Hãy áp dụng trực tiếp các thay đổi, chạy compile catalog, và trả về báo cáo với YAML frontmatter `verdict: IMPLEMENTATION_READY`.
