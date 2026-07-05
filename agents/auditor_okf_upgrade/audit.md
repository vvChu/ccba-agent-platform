## Forensic Audit Report

**Work Product**: OKF v0.1 Upgrade in `packages/ccba-legal-intel` and `scripts/validate_docs.py`
**Profile**: General Project (Development Mode)
**Verdict**: CLEAN

### Phase Results

#### Phase 1: Source Code Analysis
1. **Hardcoded output detection**: PASS — No hardcoded test results, expected output strings, or bypassed validations were found in the codebase.
2. **Facade detection**: PASS — Modules like `ccba_legal.packager`, `ccba_legal.parser`, `ccba_legal.registry`, and `scripts/validate_docs.py` implement genuine business and analytical logic (regex, bs4, LLM prompts).
3. **Pre-populated artifact detection**: PASS — No pre-populated log files, result files, or other validation artifacts were found in the workspace.

#### Phase 2: Behavioral Verification
4. **Build and run**: FAIL — While 43 test cases passed, 2 regression test failures were detected in the newly added `test_okf_upgrade_adversarial.py` suite.
5. **Output verification**: PASS — Verified that anchors (regex-based), HTML table flattening (virtual 2D grid), cost formulas (standardized using LLM prompts), and registry updates (`legal_registry.yaml` updating via registry manager) are computed dynamically.
6. **Dependency audit**: PASS — Third-party library usage (BeautifulSoup, PyYAML) is restricted to data extraction. LLM calls are routed through the internal package `ccba-ai` targeting the Spark LiteLLM API.

---

### Evidence

#### 1. Test Failure logs (uv run pytest packages/ccba-legal-intel/tests/ scripts/tests/)
```text
================================== FAILURES ===================================
______________________________ test_empty_table _______________________________

    def test_empty_table():
        packager = OKFBundlePackager(Path())
    
        # Case 1: Empty table tag
        html1 = "<table></table>"
        soup1 = BeautifulSoup(html1, "html.parser").find("table")
        grid1, is_complex1, num_rows1 = packager.flatten_html_table(soup1)
        assert grid1 == []
        assert is_complex1 is False
        assert num_rows1 == 0
        assert packager.grid_to_markdown(grid1) == ""
        assert packager.grid_to_csv(grid1) == ""
        assert packager.grid_to_json(grid1) == "[]"
    
        # Case 2: Table with only empty tr
        html2 = "<table><tr></tr></table>"
        soup2 = BeautifulSoup(html2, "html.parser").find("table")
        grid2, is_complex2, num_rows2 = packager.flatten_html_table(soup2)
        assert grid2 == [[]]
        assert is_complex2 is False
        assert num_rows2 == 1
>       assert packager.grid_to_markdown(grid2) == ""
E       AssertionError: assert '|  |\n|  |' == ''
E         
E         + |  |
E         + |  |

packages\ccba-legal-intel\tests\test_okf_upgrade_adversarial.py:32: AssertionError
_______________________ test_invalid_latex_expressions ________________________

    def test_invalid_latex_expressions():
        # Case 1: Paragraph with cost keywords but no formula
        mock_ai = MagicMock()
        mock_ai.chat.return_value = "Chi phí này được tính toán theo quy định của pháp luật hiện hành."
        engine = LegalAnalysisEngine(ai_client=mock_ai)
    
        text = "Chi phí này được tính toán theo quy định của pháp luật hiện hành."
        processed = engine.standardize_formulas(text)
        # has_formula will be True because of "tính toán" and "chi phí"
>       mock_ai.chat.assert_called_once()
E       AssertionError: Expected 'chat' to have been called once. Called 0 times.

packages\ccba-legal-intel\tests\test_okf_upgrade_adversarial.py:106: AssertionError
=========================== short test summary info ===========================
FAILED packages/ccba-legal-intel/tests/test_okf_upgrade_adversarial.py::test_empty_table
FAILED packages/ccba-legal-intel/tests/test_okf_upgrade_adversarial.py::test_invalid_latex_expressions
======================== 2 failed, 43 passed in 6.24s =========================
```

#### 2. Analysis of Test Failures / Regressions
* **`test_empty_table` regression**:
  The new implementation of `grid_to_markdown` in `packager.py` returns `|  |\n|  |` for `[[]]`, whereas the adversarial test expects `""` for a table with no columns.
* **`test_invalid_latex_expressions` regression**:
  The new implementation of `standardize_formulas` in `parser.py` restricts LLM calls by checking if `công thức`, `tính theo`, or `tính bằng` is present in the paragraph loop. The test `test_invalid_latex_expressions` contains `"Chi phí này được tính toán..."` which triggers the overall function but gets skipped in the paragraph loop since it doesn't contain specific formula-trigger keywords, causing the LLM not to be queried (0 calls instead of 1).

*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*
