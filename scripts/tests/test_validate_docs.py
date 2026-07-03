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
        hrefs = [l[2] for l in links]
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


if __name__ == "__main__":
    unittest.main()
