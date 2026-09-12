---
name: ccba-codebase-design
description: Shared vocabulary for designing deep modules (locality, depth, leverage,
  seams) to improve testability and code quality. Reference skill.
disable-model-invocation: true
category: engineering
user-invocable: true
command: /ccba-codebase-design
gpi:
  s: 4.0
  k: 3.0
  a: 1.0
  p: 1.0
keywords:
- ccba-codebase-design
- deep-module
- seam
- interface
- adapter
- leverage
- locality
metadata:
  author: CCBA
  version: 1.2.0
bundle: _core
tier: kernel
triggers:
- ccba-codebase-design
- deep-module
- seam
- interface
- adapter
- leverage
- locality
- codebase design
- deep module
- module sâu
- software design
- ccba-improve-codebase-architecture
- improve-codebase-architecture
---

# Codebase Design

> **Loại Kỹ Năng:** **Reference Skill (Kỹ Năng Tham Chiếu & Từ Điển Chuẩn Mực)**  
> **Quy Tắc Dừng Cứng (Hard Stopping Rule):** Kỹ năng này không phải là Driver Workflow tự hành. Khi được gọi độc lập mà không chỉ định rõ module mục tiêu, Agent chỉ hiển thị bộ từ vựng và dừng lại để định hướng sang Driver Skills phù hợp (`/ccba-implement`, `/ccba-grilling`).

Design **deep modules**: a lot of behaviour behind a small interface, placed at a clean seam, testable through that interface. Use this language and these principles wherever code is being designed or restructured. The aim is leverage for callers, locality for maintainers, and testability for everyone.

## Glossary

Use these terms exactly — don't substitute "component," "service," "API," or "boundary." Consistent language is the whole point.

**Module** — anything with an interface and an implementation. Deliberately scale-agnostic: a function, class, package, or tier-spanning slice. _Avoid_: unit, component, service.

**Interface** — everything a caller must know to use the module correctly: the type signature, but also invariants, ordering constraints, error modes, required configuration, and performance characteristics. _Avoid_: API, signature (too narrow — they refer only to the type-level surface).

**Implementation** — what's inside a module, its body of code. Distinct from **Adapter**: a thing can be a small adapter with a large implementation (a Postgres repo) or a large adapter with a small implementation (an in-memory fake). Reach for "adapter" when the seam is the topic; "implementation" otherwise.

**Depth** — leverage at the interface: the amount of behaviour a caller (or test) can exercise per unit of interface they have to learn. A module is **deep** when a large amount of behaviour sits behind a small interface, **shallow** when the interface is nearly as complex as the implementation.

**Seam** _(Michael Feathers)_ — a place where you can alter behaviour without editing in that place; the *location* at which a module's interface lives. Where to put the seam is its own design decision, distinct from what goes behind it. _Avoid_: boundary (overloaded with DDD's bounded context).

**Adapter** — a concrete thing that satisfies an interface at a seam. Describes *role* (what slot it fills), not substance (what's inside).

**Leverage** — what callers get from depth: more capability per unit of interface they learn. One implementation pays back across N call sites and M tests.

**Locality** — what maintainers get from depth: change, bugs, knowledge, and verification concentrate in one place rather than spreading across callers. Fix once, fixed everywhere.

## Deep vs shallow

**Deep module** = small interface + lots of implementation:

```
┌─────────────────────┐
│   Small Interface   │  ← Few methods, simple params
├─────────────────────┤
│                     │
│  Deep Implementation│  ← Complex logic hidden
│                     │
└─────────────────────┘
```

**Shallow module** = large interface + little implementation (avoid):

```
┌─────────────────────────────────┐
│       Large Interface           │  ← Many methods, complex params
├─────────────────────────────────┤
│  Thin Implementation            │  ← Just passes through
└─────────────────────────────────┘
```

When designing an interface, ask:

- Can I reduce the number of methods?
- Can I simplify the parameters?
- Can I hide more complexity inside?

## Principles

- **Depth is a property of the interface, not the implementation.** A deep module can be internally composed of small, mockable, swappable parts — they just aren't part of the interface. A module can have **internal seams** (private to its implementation, used by its own tests) as well as the **external seam** at its interface.
- **The deletion test.** Imagine deleting the module. If complexity vanishes, it was a pass-through. If complexity reappears across N callers, it was earning its keep.
- **The interface is the test surface.** Callers and tests cross the same seam. If you want to test *past* the interface, the module is probably the wrong shape.
- **One adapter means a hypothetical seam. Two adapters means a real one.** Don't introduce a seam unless something actually varies across it.

## Designing for testability

Good interfaces make testing natural:

1. **Accept dependencies, don't create them.**

   ```typescript
   // Testable (TypeScript)
   function processOrder(order, paymentGateway) {}

   // Hard to test
   function processOrder(order) {
     const gateway = new StripeGateway();
   }
   ```

2. **Return results, don't produce side effects.**

   ```typescript
   // Testable (TypeScript)
   function calculateDiscount(cart): Discount {}

   // Hard to test
   function applyDiscount(cart): void {
     cart.total -= discount;
   }
   ```

3. **Small surface area.** Fewer methods = fewer tests needed. Fewer params = simpler test setup.

## Deep Seams Pattern in Python (Protocol, DI & ADR-0035 Boundaries)

Trong hệ sinh thái Python Monorepo, việc thiết kế Deep Seams tuân thủ nghiêm ngặt nguyên tắc **Accept dependencies**, trừu tượng hóa bằng `typing.Protocol`, và ranh giới module rõ ràng:

```python
from __future__ import annotations

from typing import Protocol, runtime_checkable

# 1. Seam Definition (Protocol): Bề mặt giao diện tối giản tại Seam
@runtime_checkable
class AuditStorage(Protocol):
    """Deep Seam: Interface trừu tượng cho tầng lưu trữ audit."""
    def save_audit(self, payload: dict[str, object]) -> str: ...

# 2. Deep Module: Logic nghiệp vụ phức tạp ẩn sau một giao diện gọn gàng
class QCAuditService:
    """Deep Module: Đóng gói toàn bộ validation, checksum, và format.
    
    Nhận dependency qua __init__ thay vì tự khởi tạo (Dependency Injection).
    """
    def __init__(self, storage: AuditStorage) -> None:
        self._storage = storage  # Injected adapter

    def audit_document(self, doc_path: str) -> dict[str, object]:
        # Phức tạp nội bộ (phân tích, OCR, kiểm tra quy chuẩn) được che giấu
        report = {"path": doc_path, "status": "VERIFIED"}
        audit_id = self._storage.save_audit(report)
        report["audit_id"] = audit_id
        return report

# 3. Ranh giới Gói (Package Boundary - ADR-0035 & PEP 328):
# packages/my_package/__init__.py chỉ export public seam:
# __all__ = ["QCAuditService", "AuditStorage"]
# Chi tiết nội bộ (_internal.py hoặc sqlite_adapter.py) được giữ kín
```

**So sánh với Anti-pattern (Shallow Module & Hard to test):**
```python
# Shallow & Bypassing Seam (KHÔNG NÊN DÙNG):
class ShallowAuditService:
    def __init__(self) -> None:
        # Tự tạo kết nối cứng tới implementation, bypass private module
        from my_package._internal import ConcreteDatabase
        self.db = ConcreteDatabase()  # Rất khó mock/test độc lập
```

## Relationships

- A **Module** has exactly one **Interface** (the surface it presents to callers and tests).
- **Depth** is a property of a **Module**, measured against its **Interface**.
- A **Seam** is where a **Module**'s **Interface** lives.
- An **Adapter** sits at a **Seam** and satisfies the **Interface**.
- **Depth** produces **Leverage** for callers and **Locality** for maintainers.

## Rejected framings

- **Depth as ratio of implementation-lines to interface-lines** (Ousterhout): rewards padding the implementation. We use depth-as-leverage instead.
- **"Interface" as the TypeScript `interface` keyword or a class's public methods**: too narrow — interface here includes every fact a caller must know.
- **"Boundary"**: overloaded with DDD's bounded context. Say **seam** or **interface**.

## Going deeper

- **Deepening a cluster given its dependencies** — see [deepening.md](references/deepening.md): dependency categories, seam discipline, and replace-don't-layer testing.
- **Exploring alternative interfaces** — see [design_it_twice.md](references/design_it_twice.md): spin up parallel sub-agents (max 3) to design the interface several radically different ways, then compare on depth, locality, and seam placement.

## Progressive Disclosure & Reference Index (Level 3)

Khi thực thi các tác vụ chuyên sâu, Agent sử dụng công cụ `view_file` để nạp hướng dẫn chi tiết theo nhu cầu:

| Tệp Tham Chiếu | Ngữ Cảnh Triệu Hồi & Mục Đích Sử Dụng |
| :--- | :--- |
| `references/codebase_refactor_guide.md` | Cẩm nang rà soát module sâu và 5 Cổng phản biện kiến trúc mã nguồn |
| `references/deepening.md` | Phân loại dependency và kỷ luật làm sâu module |
| `references/design_it_twice.md` | Thiết kế 2-3 phương án giao diện đối chiếu (max 3 subagents) |
| `references/html_report_template.md` | Mẫu HTML báo cáo trực quan với Tailwind & Mermaid |

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*

*Nội dung này được tạo bởi AI Agent và cần được xem xét bởi chuyên gia pháp lý và kỹ thuật trước khi áp dụng.*
