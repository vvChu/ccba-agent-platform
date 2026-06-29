from pathlib import Path


class LinkPatcher:
    """Core utility to patch and standardize relative links to appendices inside markdown files."""

    def __init__(self) -> None:
        pass

    def patch_links(self, target_path: Path) -> list[Path]:
        """
        Scans and standardizes relative links (e.g. from appendices/ to ./appendices/) in markdown files.

        Args:
            target_path: Path to a markdown file or directory containing markdown files.

        Returns:
            A list of Paths of files that were modified.
        """
        files_to_patch: list[Path] = []
        modified_files = []

        if not target_path.exists():
            return []

        if target_path.is_dir():
            files_to_patch.extend(target_path.glob("*.md"))
        else:
            files_to_patch.append(target_path)

        for fpath in files_to_patch:
            with open(fpath, encoding="utf-8") as f:
                content = f.read()

            # Replace (appendices/ with (./appendices/
            new_content = content.replace("(appendices/", "(./appendices/")

            if new_content != content:
                with open(fpath, "w", encoding="utf-8") as f:
                    f.write(new_content)
                modified_files.append(fpath)

        return modified_files
