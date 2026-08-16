#!/usr/bin/env python3
"""demo_vbhn_delta_patch.py - Demonstrates VBHNEngine Delta Patching on Vietnamese Construction Decrees."""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure utf-8 stdout
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Add package root to sys.path

package_root = Path(__file__).resolve().parent.parent.parent / "packages" / "ccba-legal-intel" / "src"
if str(package_root) not in sys.path:
    sys.path.insert(0, str(package_root))

from ccba_legal import (
    DeltaPatch,
    DeltaPatchItem,
    MergedLegalDocument,
    PatchAction,
    VBHNEngine,
)


def run_vbhn_demo() -> MergedLegalDocument:
    """Executes a multi-stage VBHN consolidation demo simulating ND 06/2021 -> ND 35/2023 -> ND 175/2024 -> ND 14/2026."""
    print("=" * 70)
    print("🏛️ THÍ NGHIỆM 2: CHẠY THỬ BỘ MÁY HỢP NHẤT VĂN BẢN (VBHN DELTA PATCH)")
    print("=" * 70)

    # 1. Văn bản gốc: Nghị định 06/2021/NĐ-CP
    base_text = """# NGHỊ ĐỊNH 06/2021/NĐ-CP: QUY ĐỊNH CHI TIẾT VỀ QUẢN LÝ CHẤT LƯỢNG CÔNG TRÌNH

### Điều 1. Phạm vi điều chỉnh
Nghị định này quy định chi tiết một số nội dung về quản lý chất lượng, thi công xây dựng và bảo trì công trình xây dựng.

### Điều 12. Quản lý chất lượng thiết kế xây dựng công trình
1. Nhà thầu thiết kế có trách nhiệm lập hồ sơ thiết kế theo đúng quy chuẩn, tiêu chuẩn áp dụng.
2. Chủ đầu tư có trách nhiệm nghiệm thu hồ sơ thiết kế xây dựng trước khi trình thẩm định.
3. Hồ sơ thiết kế thực hiện dưới dạng bản vẽ giấy hoặc tệp số tĩnh 2D (PDF).

### Điều 24. Kiểm tra công tác nghiệm thu công trình xây dựng
1. Cơ quan chuyên môn về xây dựng kiểm tra công tác nghiệm thu của chủ đầu tư đối với công trình cấp I, cấp đặc biệt.
2. Thời hạn kiểm tra không quá 30 ngày kể từ ngày nhận đủ hồ sơ đề nghị.

### Điều 35. Quy định về chứng chỉ hành nghề của cá nhân quản lý dự án
1. Cá nhân đảm nhận chức danh giám đốc quản lý dự án phải có chứng chỉ hành nghề quản lý dự án hạng tương ứng.
2. Chứng chỉ do Sở Xây dựng hoặc Bộ Xây dựng cấp theo quy định.

### Điều 42. Trách nhiệm của chủ đầu tư trong giải quyết sự cố công trình
1. Khi xảy ra sự cố, chủ đầu tư phải báo cáo ngay bằng văn bản cho Ủy ban nhân dân cấp tỉnh và Bộ Xây dựng trong vòng 24 giờ.
"""

    print("\n📄 1. NẠP VĂN BẢN GỐC (Base Document: Nghị định 06/2021/NĐ-CP)")
    print(f"- Tổng số điều/khoản gốc: 5 Điều")

    # 2. Tạo DeltaPatch đa tầng kết hợp từ NĐ 35/2023, NĐ 175/2024 và NĐ 14/2026
    patch = DeltaPatch(
        target_doc_id="06/2021/ND-CP",
        amending_doc_id="19/VBHN-BXD-2026",
        patches=[
            # Sửa đổi Điều 12 khoản 3: Bổ sung bắt buộc áp dụng mô hình BIM (theo NĐ 175/2024)
            DeltaPatchItem(
                node_id="dieu-12",
                action=PatchAction.REPLACE,
                new_content="""### Điều 12. Quản lý chất lượng thiết kế xây dựng công trình
1. Nhà thầu thiết kế có trách nhiệm lập hồ sơ thiết kế theo đúng quy chuẩn, tiêu chuẩn áp dụng.
2. Chủ đầu tư có trách nhiệm nghiệm thu hồ sơ thiết kế xây dựng trước khi trình cơ quan chuyên môn thẩm định.
3. Hồ sơ thiết kế bắt buộc lập trên Mô hình thông tin công trình (BIM) đối với công trình cấp I, cấp đặc biệt và công trình sử dụng vốn đầu tư công theo lộ trình quy định.""",
                citation="Khoản 2 Điều 1 Nghị định 175/2024/NĐ-CP",
            ),
            # Sửa đổi Điều 24: Rút ngắn thời hạn kiểm tra và phân định thẩm quyền (theo NĐ 35/2023 & NĐ 14/2026)
            DeltaPatchItem(
                node_id="dieu-24",
                action=PatchAction.REPLACE,
                new_content="""### Điều 24. Kiểm tra công tác nghiệm thu công trình xây dựng
1. Cơ quan chuyên môn về xây dựng kiểm tra công tác nghiệm thu của chủ đầu tư đối với công trình thuộc diện thẩm định thiết kế triển khai sau thiết kế cơ sở.
2. Thời hạn kiểm tra là không quá 20 ngày (công trình cấp I, đặc biệt) hoặc 14 ngày (các công trình còn lại) kể từ ngày nhận đủ hồ sơ hợp lệ.""",
                citation="Khoản 4 Điều 1 Nghị định 35/2023/NĐ-CP và Điều 2 Nghị định 14/2026/NĐ-CP",
            ),
            # Bãi bỏ Điều 35: Bãi bỏ chứng chỉ hành nghề cá nhân QLDA (theo NĐ 212/2026 / NĐ 14/2026)
            DeltaPatchItem(
                node_id="dieu-35",
                action=PatchAction.ABROGATE,
                citation="Điều 5 Nghị định 14/2026/NĐ-CP (bãi bỏ quy định chứng chỉ hành nghề QLDA cá nhân)",
            ),
            # Bổ sung Điều 12a: Quy chuẩn nghiệm thu mô hình số và cơ sở dữ liệu mở (theo NĐ 175/2024)
            DeltaPatchItem(
                node_id="dieu-12",
                action=PatchAction.INSERT_AFTER,
                new_content="""### Điều 12a. Yêu cầu nghiệm thu và bàn giao Mô hình thông tin công trình (BIM)
1. Mô hình BIM bàn giao phải tuân thủ chuẩn trao đổi dữ liệu mở IFC (ISO 16739) và phân loại cấu kiện Uniclass 200.
2. Dữ liệu phi hình học (Qto, Pset) phải được liên kết đồng nhất với nhật ký thi công điện tử.""",
                citation="Bổ sung theo Khoản 3 Điều 1 Nghị định 175/2024/NĐ-CP",
            ),
        ],
    )

    print("\n🔧 2. TỔNG HỢP DELTA PATCHES:")
    for idx, p in enumerate(patch.patches, 1):
        print(f"  [{idx}] Hành động: {p.action.value:<12} | Vị trí: {p.node_id:<10} | Nguồn: {p.citation}")

    # 3. Kích hoạt VBHNEngine
    print("\n⚡ 3. KÍCH HOẠT VBHN ENGINE (AST Parsing -> Delta Patching -> Tree Merge -> Visual Diff)")
    engine = VBHNEngine()
    
    out_dir = Path("d:/GitHubProjects/ccba-agent-platform/.md")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "VBHN_ND06_2026_demo.md"

    result = engine.merge_documents(
        base_doc=base_text,
        amending_doc=patch,
        doc_meta={
            "title": "VĂN BẢN HỢP NHẤT 19/VBHN-BXD (2026): HỢP NHẤT NGHỊ ĐỊNH 06/2021/NĐ-CP",
            "jurisdiction": "Bộ Xây dựng",
            "effective_date": "2026-07-01",
        },
        output_path=out_file,
    )

    print("\n📊 4. KẾT QUẢ HỢP NHẤT VĂN BẢN:")
    print(f"- Tiêu đề văn bản VBHN : {result.title}")
    print(f"- Số điều thay thế (Replaced) : {result.patch_summary.get('replaced', 0)}")
    print(f"- Số điều bổ sung  (Inserted) : {result.patch_summary.get('inserted', 0)}")
    print(f"- Số điều bãi bỏ   (Abrogated): {result.patch_summary.get('abrogated', 0)}")
    print(f"- File xuất bản        : {out_file}")

    print("\n" + "=" * 70)
    print("📜 TRÍCH ĐOẠN VISUAL DIFF MARKDOWN (Tệp VBHN):")
    print("=" * 70)
    for line in result.content.splitlines():
        if any(marker in line for marker in ["### Điều", "~~", "BIM", "bãi bỏ", "bổ sung", "Sửa đổi"]):
            print(f"  {line}")

    print("\n✅ THÍ NGHIỆM VBHN DELTA PATCH HOÀN TẤT THÀNH CÔNG!")
    print("=" * 70)
    return result


if __name__ == "__main__":
    run_vbhn_demo()
