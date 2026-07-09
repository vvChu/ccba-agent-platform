import tempfile
import unittest
from pathlib import Path

from scripts.validate_docs import (
    scan_orphan_files,
    validate_markdown_file,
)


class TestValidateDocsAdversarial(unittest.TestCase):
    def test_malformed_frontmatter_in_okf(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            bundle_dir = tmppath / ".md" / "legal_docs" / "test_slug"
            bundle_dir.mkdir(parents=True, exist_ok=True)

            # Case 1: Empty frontmatter block
            empty_fm_file = bundle_dir / "empty_fm.md"
            with open(empty_fm_file, "w", encoding="utf-8") as f:
                f.write("---\n---\nBody content.")

            issues = validate_markdown_file(empty_fm_file, [], set(), tmppath)
            fm_issues = [x[2] for x in issues["okf_frontmatter"]]
            self.assertTrue(
                any("Missing required field" in err for err in fm_issues)
                or any("Missing YAML frontmatter" in err for err in fm_issues)
            )

            # Case 2: Syntax Error in YAML
            bad_yaml_file = bundle_dir / "bad_yaml.md"
            with open(bad_yaml_file, "w", encoding="utf-8") as f:
                f.write("---\ntype:: invalid: yaml:\n---\nBody content.")

            issues = validate_markdown_file(bad_yaml_file, [], set(), tmppath)
            fm_issues = [x[2] for x in issues["okf_frontmatter"]]
            # Since YAML parsing fails, it returns None frontmatter, triggering the Missing Frontmatter error
            self.assertIn("Missing YAML frontmatter for OKF Bundle file", fm_issues)

            # Case 3: List instead of Dict in YAML
            list_yaml_file = bundle_dir / "list_yaml.md"
            with open(list_yaml_file, "w", encoding="utf-8") as f:
                f.write("---\n- item1\n- item2\n---\nBody content.")

            issues = validate_markdown_file(list_yaml_file, [], set(), tmppath)
            fm_issues = [x[2] for x in issues["okf_frontmatter"]]
            # Since it's not a dict, it's treated as missing frontmatter
            self.assertIn("Missing YAML frontmatter for OKF Bundle file", fm_issues)

    def test_circular_absolute_links(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            bundle_dir = tmppath / ".md" / "legal_docs" / "test_slug"
            bundle_dir.mkdir(parents=True, exist_ok=True)

            # Create doc1 linking to /doc2.md
            doc1 = bundle_dir / "doc1.md"
            with open(doc1, "w", encoding="utf-8") as f:
                f.write("""---
type: Decree
resource: res1
status: current
timestamp: 2026-07-05T00:00:00Z
---
Link to doc 2: [Doc 2](/doc2.md)
""")

            # Create doc2 linking to /doc1.md
            doc2 = bundle_dir / "doc2.md"
            with open(doc2, "w", encoding="utf-8") as f:
                f.write("""---
type: Decree
resource: res2
status: current
timestamp: 2026-07-05T00:00:00Z
---
Link to doc 1: [Doc 1](/doc1.md)
""")

            # Verify that scan_orphan_files resolves circular dependencies without hanging
            # Both are referenced, so neither is an orphan
            orphans = scan_orphan_files(bundle_dir, tmppath)
            self.assertEqual(len(orphans), 0)

            # Verify validate_markdown_file does not crash on circular reference
            issues1 = validate_markdown_file(doc1, [], set(), tmppath)
            issues2 = validate_markdown_file(doc2, [], set(), tmppath)

            self.assertEqual(len(issues1["okf_links"]), 0)
            self.assertEqual(len(issues2["okf_links"]), 0)

    def test_missing_registry_mapping(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            bundle_dir = tmppath / ".md" / "legal_docs" / "test_slug"
            bundle_dir.mkdir(parents=True, exist_ok=True)

            # Link referencing an anchor of an unmapped target file
            md_file = bundle_dir / "source.md"
            with open(md_file, "w", encoding="utf-8") as f:
                f.write("""---
type: Decree
resource: res1
status: current
timestamp: 2026-07-05T00:00:00Z
---
Link to unmapped file: [Sec 1](/nonexistent_target.md#d1k1)
""")

            # Validate with empty registry_map (None)
            issues = validate_markdown_file(md_file, [], set(), tmppath, registry_map=None)
            # Should not crash and should report file does not exist (not a conflict since registry is missing)
            self.assertEqual(len(issues["okf_conflicts"]), 0)
            self.assertTrue(any("does not exist" in x[2] for x in issues["okf_links"]))
