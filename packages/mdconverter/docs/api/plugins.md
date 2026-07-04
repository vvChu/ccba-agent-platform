# Plugins API Reference

## Vietnamese Legal Documents Plugin

::: mdconverter.plugins.vn_legal.detector
    options:
      show_root_heading: true
      members:
        - is_legal_document
        - get_document_type

---

::: mdconverter.plugins.vn_legal.processor
    options:
      show_root_heading: true
      members:
        - VNLegalProcessor

---

::: mdconverter.plugins.vn_legal.linter
    options:
      show_root_heading: true
      members:
        - VNLegalLinter
        - LintIssue
