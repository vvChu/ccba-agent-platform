import tempfile
import unittest
from pathlib import Path

from scripts.validate_docs import (
    extract_code_references,
    extract_env_variables,
    extract_internal_links,
    validate_markdown_file,
)


class TestValidateDocs(unittest.TestCase):
    def test_extract_code_references(self):
        content = """
        This is a reference to `my_func()` in the code.
        Also check `MyClass` definition.
        Ignore `true`, `const` and `readme`.
        """
        refs = extract_code_references(content)
        ref_names = [r[1] for r in refs]
        self.assertIn("my_func()", ref_names)
        self.assertIn("MyClass", ref_names)
        self.assertNotIn("true", ref_names)
        self.assertNotIn("const", ref_names)

    def test_extract_internal_links(self):
        content = """
        Check [Installation Guide](./install.md) for help.
        Anchor [Section](#some-header) is ignored.
        External link [Google](https://google.com) is ignored.
        """
        links = extract_internal_links(content)
        hrefs = [item[2] for item in links]
        self.assertIn("./install.md", hrefs)
        self.assertNotIn("#some-header", hrefs)
        self.assertNotIn("https://google.com", hrefs)

    def test_extract_env_variables(self):
        content = """
        Setup the `API_KEY` in environment.
        Or use $PORT to configure port.
        Ignore `NODE_ENV` and $ARGUMENTS.
        """
        vars = extract_env_variables(content)
        var_names = [v[1] for v in vars]
        self.assertIn("API_KEY", var_names)
        self.assertIn("PORT", var_names)
        self.assertNotIn("NODE_ENV", var_names)
        self.assertNotIn("ARGUMENTS", var_names)

    def test_validate_markdown_file_integration(self):
        # Create a temporary environment to run verification
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            # Create a mock source code file
            src_file = tmppath / "my_code.py"
            with open(src_file, "w", encoding="utf-8") as f:
                f.write("def my_func(): pass\nclass MyClass: pass\n")

            # Create a mock env example
            env_file = tmppath / ".env.example"
            with open(env_file, "w", encoding="utf-8") as f:
                f.write("API_KEY=12345\n")

            # Create an existing target link file
            target_link = tmppath / "install.md"
            target_link.touch()

            # Create the test markdown file to validate
            md_file = tmppath / "doc.md"
            with open(md_file, "w", encoding="utf-8") as f:
                f.write("""
                Reference `my_func()` and `MyClass`.
                Broken reference `non_existent_func()`.
                Link to existing [Install](./install.md).
                Link to broken [Setup](./setup.md).
                Env key `API_KEY` (valid) and `SECRET_KEY` (invalid).
                """)

            env_vars = {"API_KEY"}
            issues = validate_markdown_file(md_file, [tmppath], env_vars, tmppath)

            # Verify code ref issues
            code_issues = [x[1] for x in issues["code_refs"]]
            self.assertIn("non_existent_func()", code_issues)
            self.assertNotIn("my_func()", code_issues)
            self.assertNotIn("MyClass", code_issues)

            # Verify link issues
            link_issues = [x[1] for x in issues["links"]]
            self.assertIn("./setup.md", link_issues)
            self.assertNotIn("./install.md", link_issues)

            # Verify env issues
            env_issues = [x[1] for x in issues["env_vars"]]
            self.assertIn("SECRET_KEY", env_issues)
            self.assertNotIn("API_KEY", env_issues)

    def test_okf_frontmatter_validation(self):
        # Create a temp directory simulating a bundle structure
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            # File inside legal_docs/<slug>/ with missing frontmatter
            bundle_dir = tmppath / ".md" / "legal_docs" / "test_slug"
            bundle_dir.mkdir(parents=True, exist_ok=True)

            # Case 1: missing frontmatter
            no_fm_file = bundle_dir / "doc1.md"
            with open(no_fm_file, "w", encoding="utf-8") as f:
                f.write("This is a document without frontmatter.")

            issues = validate_markdown_file(no_fm_file, [], set(), tmppath)
            fm_issues = [x[2] for x in issues["okf_frontmatter"]]
            self.assertIn("Missing YAML frontmatter for OKF Bundle file", fm_issues)

            # Case 2: invalid frontmatter type and missing fields
            bad_fm_file = bundle_dir / "doc2.md"
            with open(bad_fm_file, "w", encoding="utf-8") as f:
                f.write(
                    "---\ntype: InvalidType\ntimestamp: 2026-07-05T00:00:00Z\n---\nBody content."
                )

            issues = validate_markdown_file(bad_fm_file, [], set(), tmppath)
            fm_issues = [x[2] for x in issues["okf_frontmatter"]]
            # Invalid type error
            self.assertTrue(any("Invalid type:" in err for err in fm_issues))
            # Missing resource error
            self.assertTrue(any("Missing required field: 'resource'" in err for err in fm_issues))
            # Missing status/document_number error
            self.assertTrue(
                any(
                    "Missing required field: 'status' or 'document_number'" in err
                    for err in fm_issues
                )
            )

            # Case 3: valid frontmatter
            good_fm_file = bundle_dir / "doc3.md"
            with open(good_fm_file, "w", encoding="utf-8") as f:
                f.write(
                    "---\ntype: Decree\nresource: res123\nstatus: current\ntimestamp: 2026-07-05T00:00:00Z\n---\nBody."
                )

            issues = validate_markdown_file(good_fm_file, [], set(), tmppath)
            self.assertEqual(len(issues["okf_frontmatter"]), 0)

    def test_okf_cross_links_validation(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            bundle_dir = tmppath / ".md" / "legal_docs" / "test_slug"
            bundle_dir.mkdir(parents=True, exist_ok=True)

            # Create a target file that exists
            target_file = bundle_dir / "target.md"
            target_file.touch()

            # Create a document with:
            # - a valid absolute bundle link: [/target.md]
            # - a broken absolute bundle link: [/broken.md]
            # - a relative link that resolves inside the bundle: [relative](target.md)
            #   (violates the absolute cross-link rule)
            md_file = bundle_dir / "source.md"
            with open(md_file, "w", encoding="utf-8") as f:
                f.write("""---
type: Decree
resource: res123
status: current
timestamp: 2026-07-05T00:00:00Z
---
Valid absolute link: [Label](/target.md)
Broken absolute link: [Label](/broken.md)
Relative link inside bundle: [Label](target.md)
""")
            issues = validate_markdown_file(md_file, [], set(), tmppath)

            okf_link_issues = issues["okf_links"]
            # We expect the broken absolute link to be reported
            broken_paths = [x[1] for x in okf_link_issues if "does not exist" in x[2]]
            self.assertIn("/broken.md", broken_paths)

            # We expect the relative link inside the bundle to be reported as violating absolute rule
            rel_paths = [x[1] for x in okf_link_issues if "must start with '/'" in x[2]]
            self.assertIn("target.md", rel_paths)

    def test_orphan_files_scanning(self):
        from scripts.validate_docs import scan_orphan_files

        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            bundle_dir = tmppath / ".md" / "legal_docs" / "test_slug"
            bundle_dir.mkdir(parents=True, exist_ok=True)

            # doc1 links to doc2
            doc1 = bundle_dir / "doc1.md"
            with open(doc1, "w", encoding="utf-8") as f:
                f.write("[Link](/doc2.md)")

            # doc2 is linked, so it's not an orphan
            doc2 = bundle_dir / "doc2.md"
            doc2.touch()

            # doc3 has no links to it, so it is an orphan
            doc3 = bundle_dir / "doc3.md"
            doc3.touch()

            orphans = scan_orphan_files(bundle_dir, tmppath)
            orphan_stems = [p.stem for p in orphans]
            self.assertIn("doc1", orphan_stems)  # doc1 has no links to it
            self.assertIn("doc3", orphan_stems)  # doc3 has no links to it
            self.assertNotIn("doc2", orphan_stems)  # doc2 IS linked by doc1

    def test_cross_validity_conflicts(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            bundle_dir = tmppath / ".md" / "legal_docs" / "test_slug"
            bundle_dir.mkdir(parents=True, exist_ok=True)

            target_doc = bundle_dir / "target.md"
            target_doc.touch()

            # Mock registry mapping
            registry_map = {
                target_doc.resolve(): {
                    "id": "DOC-123",
                    "clauses": {
                        "sec1": {"status": "amended", "amended_by": "DOC-999"},
                        "sec2": {"status": "superseded", "amended_by": "DOC-888"},
                        "sec3": {"status": "current"},
                    },
                }
            }

            # Case 1: link points to amended section without warning block
            md_file1 = bundle_dir / "source1.md"
            with open(md_file1, "w", encoding="utf-8") as f:
                f.write("""---
type: Decree
resource: res123
status: current
timestamp: 2026-07-05T00:00:00Z
---
Here is a link: [Sec 1](/target.md#sec1)
""")
            issues = validate_markdown_file(md_file1, [], set(), tmppath, registry_map=registry_map)
            conflict_errs = [x[2] for x in issues["okf_conflicts"]]
            self.assertTrue(any("points to amended clause 'sec1'" in err for err in conflict_errs))

            # Case 2: link points to amended section WITH warning block
            md_file2 = bundle_dir / "source2.md"
            with open(md_file2, "w", encoding="utf-8") as f:
                f.write("""---
type: Decree
resource: res123
status: current
timestamp: 2026-07-05T00:00:00Z
---
Here is a link: [Sec 1](/target.md#sec1)
> [!WARNING] This section is amended.
""")
            issues = validate_markdown_file(md_file2, [], set(), tmppath, registry_map=registry_map)
            self.assertEqual(len(issues["okf_conflicts"]), 0)

    def test_orphan_files_parent_document(self):
        from scripts.validate_docs import scan_orphan_files

        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            bundle_dir = tmppath / ".md" / "legal_docs" / "test_slug"
            bundle_dir.mkdir(parents=True, exist_ok=True)

            # parent exists in the bundle
            parent_file = bundle_dir / "parent.md"
            parent_file.touch()

            # child has parent_document field referencing parent.md
            child_file = bundle_dir / "child.md"
            with open(child_file, "w", encoding="utf-8") as f:
                f.write("---\nparent_document: parent.md\n---\n")

            # another child references non-existent parent
            broken_child = bundle_dir / "broken_child.md"
            with open(broken_child, "w", encoding="utf-8") as f:
                f.write("---\nparent_document: non_existent.md\n---\n")

            orphans = scan_orphan_files(bundle_dir, tmppath)
            orphan_stems = [p.name for p in orphans]

            # parent.md itself has no references and no parent_document, so it is an orphan
            self.assertIn("parent.md", orphan_stems)
            # child.md has parent_document that exists, so it is NOT an orphan
            self.assertNotIn("child.md", orphan_stems)
            # broken_child.md has parent_document that does not exist, so it IS an orphan
            self.assertIn("broken_child.md", orphan_stems)

    def test_orphan_files_index_full_text_exemption(self):
        from scripts.validate_docs import scan_orphan_files

        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            bundle_dir = tmppath / ".md" / "legal_docs" / "test_slug"
            bundle_dir.mkdir(parents=True, exist_ok=True)

            # index.md and full_text.md have no links or parent_document
            index_file = bundle_dir / "index.md"
            index_file.touch()

            full_text_file = bundle_dir / "full_text.md"
            full_text_file.touch()

            # normal orphan file
            normal_orphan = bundle_dir / "normal.md"
            normal_orphan.touch()

            orphans = scan_orphan_files(bundle_dir, tmppath)
            orphan_stems = [p.name for p in orphans]

            # index.md and full_text.md must be exempted
            self.assertNotIn("index.md", orphan_stems)
            self.assertNotIn("full_text.md", orphan_stems)
            # normal.md is still an orphan
            self.assertIn("normal.md", orphan_stems)


if __name__ == "__main__":
    unittest.main()
