"""Unit tests for Geofenced Dual-Pool Partitioned Retrieval and Folder Discovery (Issue #276)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from ccba_legal.federated_rag import FederatedLegalEngine
from ccba_legal.registry import LegalRegistryManager


@pytest.fixture()
def mock_legal_corpus(tmp_path: Path) -> Path:
    """Create a mock multi-jurisdiction corpus with national and provincial bundles."""
    corpus_root = tmp_path / "legal_docs"
    corpus_root.mkdir()

    # 1. National bundle: Luật Xây dựng (VN)
    b_vn = corpus_root / "01_vbpl" / "luat_xay_dung_55_2024"
    b_vn.mkdir(parents=True)
    meta_vn = {
        "doc_id": "luat_55_2024",
        "title": "Luật Xây dựng số 55/2024/QH15",
        "doc_number": "55/2024/QH15",
        "status": "effective",
        "category": "construction",
        "territory": "VN",
    }
    (b_vn / "metadata.yaml").write_text(yaml.dump(meta_vn, allow_unicode=True), encoding="utf-8")
    clauses_vn = [
        {
            "clause_id": "dieu-15",
            "title": "Điều 15. Nguyên tắc cơ bản trong hoạt động đầu tư xây dựng",
            "line_start": 1,
            "line_end": 2,
        },
        {
            "clause_id": "dieu-16",
            "title": "Điều 16. Giấy phép xây dựng trên phạm vi toàn quốc",
            "line_start": 3,
            "line_end": 4,
        },
    ]
    (b_vn / "clauses.json").write_text(json.dumps(clauses_vn, ensure_ascii=False), encoding="utf-8")
    (b_vn / "luat_55_2024.md").write_text(
        "Hoạt động đầu tư xây dựng tuân thủ quy chuẩn kỹ thuật quốc gia.\n"
        "Bảo đảm an toàn chịu lực và phòng chống cháy nổ.\n"
        "Cấp giấy phép xây dựng theo thẩm quyền quản lý nhà nước về xây dựng.\n"
        "Hồ sơ đề nghị cấp phép xây dựng theo quy định chung của Chính phủ.\n",
        encoding="utf-8",
    )

    # 2. Hanoi provincial bundle: Quyết định 38/2026/QĐ-UBND (VN-HN)
    b_hn = corpus_root / "01_vbpl" / "vn_hn_qd_38_2026"
    b_hn.mkdir(parents=True)
    meta_hn = {
        "doc_id": "vn_hn_qd_38_2026",
        "title": "Quyết định số 38/2026/QĐ-UBND TP. Hà Nội",
        "doc_number": "38/2026/QĐ-UBND",
        "status": "effective",
        "category": "decisions",
        "territory": "VN-HN",
    }
    (b_hn / "metadata.yaml").write_text(yaml.dump(meta_hn, allow_unicode=True), encoding="utf-8")
    clauses_hn = [
        {
            "clause_id": "dieu-12",
            "title": "Điều 12. Chấp thuận tổng mặt bằng tại TP. Hà Nội",
            "line_start": 1,
            "line_end": 2,
        },
        {
            "clause_id": "dieu-14",
            "title": "Điều 14. Trách nhiệm UBND cấp phường trong lấy ý kiến cộng đồng",
            "line_start": 3,
            "line_end": 4,
        },
    ]
    (b_hn / "clauses.json").write_text(json.dumps(clauses_hn, ensure_ascii=False), encoding="utf-8")
    (b_hn / "vn_hn_qd_38_2026.md").write_text(
        "Sở Xây dựng TP. Hà Nội chủ trì thẩm định quy hoạch tổng mặt bằng 1/500.\n"
        "Cơ chế một cửa tiếp nhận và giải quyết thủ tục quy hoạch xây dựng thủ đô.\n"
        "UBND phường chủ trì phối hợp lấy ý kiến cộng đồng dân cư chịu ảnh hưởng.\n"
        "Phường không có thẩm quyền thẩm định hay phê duyệt quy hoạch tổng mặt bằng.\n",
        encoding="utf-8",
    )

    # 3. HCMC provincial bundle: Quyết định 56/2025/QĐ-UBND (VN-HCM)
    b_hcm = corpus_root / "01_vbpl" / "vn_hcm_qd_56_2025"
    b_hcm.mkdir(parents=True)
    meta_hcm = {
        "doc_id": "vn_hcm_qd_56_2025",
        "title": "Quyết định số 56/2025/QĐ-UBND TP. Hồ Chí Minh",
        "doc_number": "56/2025/QĐ-UBND",
        "status": "effective",
        "category": "decisions",
        "territory": "VN-HCM",
    }
    (b_hcm / "metadata.yaml").write_text(yaml.dump(meta_hcm, allow_unicode=True), encoding="utf-8")
    clauses_hcm = [
        {
            "clause_id": "dieu-8",
            "title": "Điều 8. Phân cấp cấp phép xây dựng tại TP. Hồ Chí Minh",
            "line_start": 1,
            "line_end": 2,
        }
    ]
    (b_hcm / "clauses.json").write_text(
        json.dumps(clauses_hcm, ensure_ascii=False), encoding="utf-8"
    )
    (b_hcm / "vn_hcm_qd_56_2025.md").write_text(
        "Sở Xây dựng TP. Hồ Chí Minh cấp phép xây dựng cho công trình cấp I và cấp II.\n"
        "UBND TP. Thủ Đức và các quận huyện cấp giấy phép xây dựng công trình còn lại.\n",
        encoding="utf-8",
    )

    return corpus_root


def test_geofenced_retrieval_isolation(mock_legal_corpus: Path):
    """Test that regional search strictly prevents inter-provincial leakage (Adversarial Geofence)."""
    engine = FederatedLegalEngine(corpus_paths=[mock_legal_corpus])

    # 1. Tra cứu cho địa bàn Hà Nội (VN-HN)
    hits_hn = engine.query(
        "giấy phép xây dựng và thẩm định quy hoạch",
        jurisdiction="VN-HN",
        k=6,
    )
    assert len(hits_hn) > 0
    # Kết quả được phép chứa VN (quốc gia) và VN-HN (Hà Nội)
    for hit in hits_hn:
        assert hit["territory"] in ("VN", "VN-HN"), (
            f"Leakage detected! Got territory: {hit['territory']}"
        )
        assert hit["territory"] != "VN-HCM"

    # Kiểm tra xem có trúng hit của Hà Nội không
    has_hn = any(hit["territory"] == "VN-HN" for hit in hits_hn)
    assert has_hn is True

    # 2. Tra cứu cho địa bàn TP. Hồ Chí Minh (VN-HCM)
    hits_hcm = engine.query(
        "cấp phép xây dựng công trình",
        jurisdiction="VN-HCM",
        k=6,
    )
    assert len(hits_hcm) > 0
    # Kết quả được phép chứa VN và VN-HCM
    for hit in hits_hcm:
        assert hit["territory"] in ("VN", "VN-HCM"), (
            f"Leakage detected! Got territory: {hit['territory']}"
        )
        assert hit["territory"] != "VN-HN"

    has_hcm = any(hit["territory"] == "VN-HCM" for hit in hits_hcm)
    assert has_hcm is True


def test_geofenced_backward_compatibility_when_no_jurisdiction(mock_legal_corpus: Path):
    """Test that omitting jurisdiction retrieves across all pools without errors."""
    engine = FederatedLegalEngine(corpus_paths=[mock_legal_corpus])
    hits_all = engine.query(
        "xây dựng và thẩm định",
        jurisdiction=None,
        k=10,
    )
    assert len(hits_all) > 0
    territories = {hit["territory"] for hit in hits_all}
    # Backward-compatible query can see documents across pools
    assert "VN" in territories


def test_dual_pool_quota_allocation(mock_legal_corpus: Path):
    """Test that Dual-Pool retrieval guarantees reserved slots for local documents."""
    engine = FederatedLegalEngine(corpus_paths=[mock_legal_corpus])
    # Đặt k=4, k_local_min=2
    hits = engine.query(
        "quy hoạch và xây dựng",
        jurisdiction="VN-HN",
        k=4,
        k_local_min=2,
    )
    local_hits = [h for h in hits if h["territory"] == "VN-HN"]
    national_hits = [h for h in hits if h["territory"] == "VN"]

    assert len(local_hits) >= 1
    assert len(national_hits) >= 1
    # Check hierarchy levels
    for h in local_hits:
        assert h["hierarchy_level"] in ("LOCAL", "PROVINCIAL")
    for h in national_hits:
        assert h["hierarchy_level"] == "NATIONAL"


def test_rglob_recursive_bundle_discovery(tmp_path: Path):
    """Test that _expand_bundle_dirs discovers bundles at arbitrary folder depths via rglob."""
    root = tmp_path / "deep_docs"
    # Cấu trúc lồng 3 cấp: root / level1 / level2 / bundle
    nested_bundle = root / "regional" / "northern" / "hanoi_bundle"
    nested_bundle.mkdir(parents=True)
    (nested_bundle / "metadata.yaml").write_text("doc_id: nested_test\n", encoding="utf-8")

    engine = FederatedLegalEngine(corpus_paths=[root])
    discovered_paths = [p.name for p in engine._corpus_paths]
    assert "hanoi_bundle" in discovered_paths


def test_registry_territory_filter(tmp_path: Path):
    """Test LegalRegistryManager filters by territory (VN + requested territory)."""
    reg_file = tmp_path / "legal_registry.yaml"
    data = {
        "metadata": {"version": "2.4"},
        "laws": [
            {
                "id": "LUAT-55-2024",
                "short_name": "Luật Xây dựng 2024",
                "document_number": "55/2024/QH15",
                "status": "effective",
                "territory": "VN",
            }
        ],
        "decisions": [
            {
                "id": "QD-38-HN",
                "short_name": "QĐ 38/2026 Hà Nội",
                "document_number": "38/2026/QĐ-UBND",
                "status": "effective",
                "territory": "VN-HN",
            },
            {
                "id": "QD-56-HCM",
                "short_name": "QĐ 56/2025 TP.HCM",
                "document_number": "56/2025/QĐ-UBND",
                "status": "effective",
                "territory": "VN-HCM",
            },
        ],
    }
    reg_file.write_text(yaml.dump(data, allow_unicode=True), encoding="utf-8")

    mgr = LegalRegistryManager(reg_file)

    # Filter territory VN-HN: Phải có LUAT-55-2024 (VN) và QD-38-HN (VN-HN), loại trừ QD-56-HCM
    results_hn = mgr.search(query="", territory="VN-HN")
    ids_hn = {doc["id"] for doc in results_hn}
    assert "LUAT-55-2024" in ids_hn
    assert "QD-38-HN" in ids_hn
    assert "QD-56-HCM" not in ids_hn

    # Filter territory VN-HCM: Phải có LUAT-55-2024 (VN) và QD-56-HCM (VN-HCM), loại trừ QD-38-HN
    results_hcm = mgr.search(query="", territory="VN-HCM")
    ids_hcm = {doc["id"] for doc in results_hcm}
    assert "LUAT-55-2024" in ids_hcm
    assert "QD-56-HCM" in ids_hcm
    assert "QD-38-HN" not in ids_hcm


def test_strict_national_isolation_zero_leakage(mock_legal_corpus: Path):
    """Test that national queries strictly isolate and prevent any provincial chunks from leaking."""
    engine = FederatedLegalEngine(corpus_paths=[mock_legal_corpus])

    # 1. Tra cứu với jurisdiction="VN" (National Core)
    hits_vn = engine.query(
        "quy định cấp giấy phép xây dựng và thẩm định",
        jurisdiction="VN",
        k=6,
    )
    assert len(hits_vn) > 0
    for hit in hits_vn:
        assert hit["territory"] == "VN", (
            f"Provincial leakage into national query: {hit['territory']}"
        )

    # 2. Tra cứu với jurisdiction=None (Mặc định toàn quốc)
    hits_none = engine.query(
        "quy hoạch xây dựng",
        jurisdiction=None,
        k=6,
    )
    for hit in hits_none:
        assert hit["territory"] == "VN", f"Leakage with None jurisdiction: {hit['territory']}"

    # 3. Tra cứu đa vùng với danh sách địa bàn
    hits_multi = engine.query(
        "cấp phép xây dựng và thẩm định",
        jurisdiction=["VN-HN", "VN-HCM"],
        k=6,
    )
    assert any(h["territory"] == "VN-HN" for h in hits_multi)
    assert any(h["territory"] == "VN-HCM" for h in hits_multi)


def test_mock_local_bundle_discovery_and_indexing():
    """Test that FederatedLegalEngine indexes OKF v2.4 Universal mock local bundles directly."""
    fixture_corpus = Path(__file__).parent / "fixtures" / "mock_local_bundles"
    engine = FederatedLegalEngine(corpus_paths=[fixture_corpus])
    assert len(engine._chunks) >= 2

    # Query within VN-HN: tra cứu phân cấp thẩm định quy hoạch theo QĐ 38/2026/QĐ-UBND
    results = engine.query("thẩm định điều chỉnh cục bộ quy hoạch", jurisdiction="VN-HN", k=5)
    assert len(results) > 0
    assert results[0]["territory"] == "VN-HN"
    assert "quy hoạch" in results[0]["text"].lower()


def test_federated_rag_filters_expired_documents(tmp_path: Path):
    """Test that FederatedLegalEngine excludes expired documents by default unless include_expired=True."""
    corpus_root = tmp_path / "legal_docs"
    corpus_root.mkdir()

    # 1. Expired bundle (e.g. ND 10/2021)
    b_exp = corpus_root / "01_vbpl" / "10_2021_nd_cp"
    b_exp.mkdir(parents=True)
    meta_exp = {
        "doc_id": "10_2021_nd_cp",
        "title": "Nghị định 10/2021/NĐ-CP quản lý chi phí đầu tư xây dựng",
        "doc_number": "10/2021/NĐ-CP",
        "status": "expired",
        "category": "cost",
        "territory": "VN",
    }
    (b_exp / "metadata.yaml").write_text(yaml.dump(meta_exp, allow_unicode=True), encoding="utf-8")
    clauses_exp = [
        {
            "clause_id": "dieu-1",
            "title": "Điều 1. Quản lý chi phí đầu tư xây dựng theo Nghị định 10 cũ",
            "line_start": 1,
            "line_end": 2,
        }
    ]
    (b_exp / "clauses.json").write_text(
        json.dumps(clauses_exp, ensure_ascii=False), encoding="utf-8"
    )
    (b_exp / "10_2021_nd_cp.md").write_text(
        "Quy định quản lý chi phí đầu tư xây dựng cũ theo Nghị định 10.\n",
        encoding="utf-8",
    )

    # 2. Active bundle (e.g. ND 206/2026)
    b_act = corpus_root / "01_vbpl" / "nghi_dinh_206_2026_nd_cp"
    b_act.mkdir(parents=True)
    meta_act = {
        "doc_id": "nghi_dinh_206_2026_nd_cp",
        "title": "Nghị định 206/2026/NĐ-CP quản lý chi phí đầu tư xây dựng",
        "doc_number": "206/2026/NĐ-CP",
        "status": "active",
        "category": "cost",
        "territory": "VN",
    }
    (b_act / "metadata.yaml").write_text(yaml.dump(meta_act, allow_unicode=True), encoding="utf-8")
    clauses_act = [
        {
            "clause_id": "dieu-1",
            "title": "Điều 1. Quản lý chi phí đầu tư xây dựng theo Nghị định 206 mới",
            "line_start": 1,
            "line_end": 2,
        }
    ]
    (b_act / "clauses.json").write_text(
        json.dumps(clauses_act, ensure_ascii=False), encoding="utf-8"
    )
    (b_act / "nghi_dinh_206_2026_nd_cp.md").write_text(
        "Quy định quản lý chi phí đầu tư xây dựng mới theo Nghị định 206 hiện hành.\n",
        encoding="utf-8",
    )

    engine = FederatedLegalEngine(corpus_paths=[corpus_root], embedding_enabled=False)
    assert len(engine._chunks) == 2

    # Query without include_expired: should ONLY find ND 206/2026
    default_results = engine.query("chi phí đầu tư xây dựng", k=10)
    assert len(default_results) == 1
    assert default_results[0]["document_id"] == "nghi_dinh_206_2026_nd_cp"

    # Query with include_expired=True: should find both
    all_results = engine.query("chi phí đầu tư xây dựng", k=10, include_expired=True)
    assert len(all_results) == 2
    doc_ids = {r["document_id"] for r in all_results}
    assert doc_ids == {"10_2021_nd_cp", "nghi_dinh_206_2026_nd_cp"}


def test_federated_rag_point_in_time_as_of_date(tmp_path: Path):
    """Test that FederatedLegalEngine respects historical point-in-time (as_of_date) legal validity."""
    corpus_root = tmp_path / "legal_docs"
    corpus_root.mkdir()

    # 1. Historical document: active 2021-02-09 to 2026-07-01
    b_hist = corpus_root / "01_vbpl" / "10_2021_nd_cp"
    b_hist.mkdir(parents=True)
    meta_hist = {
        "doc_id": "10_2021_nd_cp",
        "title": "Nghị định 10/2021/NĐ-CP quản lý chi phí",
        "status": "expired",
        "effective_date": "2021-02-09",
        "expiration_date": "2026-07-01",
        "category": "cost",
        "territory": "VN",
    }
    (b_hist / "metadata.yaml").write_text(
        yaml.dump(meta_hist, allow_unicode=True), encoding="utf-8"
    )
    clauses_hist = [
        {
            "clause_id": "dieu-1",
            "title": "Điều 1. Chi phí dự án 2021",
            "line_start": 1,
            "line_end": 2,
        }
    ]
    (b_hist / "clauses.json").write_text(
        json.dumps(clauses_hist, ensure_ascii=False), encoding="utf-8"
    )
    (b_hist / "10_2021_nd_cp.md").write_text(
        "Chi phí đầu tư xây dựng áp dụng cho hợp đồng 2021.\n", encoding="utf-8"
    )

    # 2. Modern document: effective from 2026-07-01 onwards
    b_mod = corpus_root / "01_vbpl" / "nghi_dinh_206_2026_nd_cp"
    b_mod.mkdir(parents=True)
    meta_mod = {
        "doc_id": "nghi_dinh_206_2026_nd_cp",
        "title": "Nghị định 206/2026/NĐ-CP quản lý chi phí",
        "status": "active",
        "effective_date": "2026-07-01",
        "expiration_date": "",
        "category": "cost",
        "territory": "VN",
    }
    (b_mod / "metadata.yaml").write_text(yaml.dump(meta_mod, allow_unicode=True), encoding="utf-8")
    clauses_mod = [
        {
            "clause_id": "dieu-1",
            "title": "Điều 1. Chi phí dự án 2026",
            "line_start": 1,
            "line_end": 2,
        }
    ]
    (b_mod / "clauses.json").write_text(
        json.dumps(clauses_mod, ensure_ascii=False), encoding="utf-8"
    )
    (b_mod / "nghi_dinh_206_2026_nd_cp.md").write_text(
        "Chi phí đầu tư xây dựng mới theo Nghị định 206.\n", encoding="utf-8"
    )

    engine = FederatedLegalEngine(corpus_paths=[corpus_root], embedding_enabled=False)

    # When querying for dispute/audit as of 2023-06-01: ND 10 was valid, ND 206 did not exist!
    res_2023 = engine.query("chi phí đầu tư xây dựng", as_of_date="2023-06-01", k=10)
    assert len(res_2023) == 1
    assert res_2023[0]["document_id"] == "10_2021_nd_cp"

    # When querying for project as of 2026-08-01: ND 10 expired, ND 206 is in force!
    res_2026 = engine.query("chi phí đầu tư xây dựng", as_of_date="2026-08-01", k=10)
    assert len(res_2026) == 1
    assert res_2026[0]["document_id"] == "nghi_dinh_206_2026_nd_cp"
