# Unit tests for Ingestion Provenance & Cross-Verification (Gate 0)
from __future__ import annotations

import unittest

from ccba_legal.provenance import (
    check_structure_alignment,
    compute_text_parity,
    normalize_text,
)


class TestProvenanceEngine(unittest.TestCase):
    def test_normalize_text(self) -> None:
        raw = 'Điều 1.   Phạm vi điều chỉnh: (Áp dụng cho mọi công trình)!'
        norm = normalize_text(raw)
        self.assertEqual(norm, 'điều 1 phạm vi điều chỉnh áp dụng cho mọi công trình')

    def test_structure_alignment_matching(self) -> None:
        pdf_text = 'Điều 1. Phạm vi\nĐiều 2. Đối tượng áp dụng\nChương I. Quy định chung'
        docx_paras = ['Điều 1. Phạm vi điều chỉnh', 'Điều 2. Đối tượng', 'Chương I. QUY ĐỊNH CHUNG']
        res = check_structure_alignment(pdf_text, docx_paras)
        self.assertEqual(res['docx_dieu_count'], 2)
        self.assertEqual(res['pdf_dieu_count'], 2)
        self.assertEqual(res['missing_in_docx'], [])
        self.assertEqual(res['chapters_pdf'], ['I'])

    def test_structure_alignment_missing_article(self) -> None:
        pdf_text = 'Điều 1. Phạm vi\nĐiều 2. Đối tượng\nĐiều 3. Giải thích từ ngữ'
        docx_paras = ['Điều 1. Phạm vi', 'Điều 2. Đối tượng']
        res = check_structure_alignment(pdf_text, docx_paras)
        self.assertEqual(res['missing_in_docx'], [3])

    def test_compute_text_parity_scanned(self) -> None:
        # If pdf text is < 200 chars, it is recognized as scanned and returns 100.0
        res = compute_text_parity('short text', ['some long docx paragraph with more than 40 chars for testing'])
        self.assertEqual(res, 100.0)

    def test_compute_text_parity_digital(self) -> None:
        pdf_text = 'Nghị định này quy định chi tiết thi hành một số điều của Luật Xây dựng năm 2025.' * 10
        docx_paras = ['Nghị định này quy định chi tiết thi hành một số điều của Luật Xây dựng năm 2025.']
        res = compute_text_parity(pdf_text, docx_paras)
        self.assertEqual(res, 100.0)
