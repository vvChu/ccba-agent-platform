import re
import urllib.parse
from pathlib import Path


def main():
    md_dir = Path("d:/GitHubProjects/ccba-agent-platform/.md")
    if not md_dir.exists():
        print(f"Directory {md_dir} does not exist.")
        return

    # Find all files starting with [
    files = list(md_dir.glob("[Fi_*"))
    if not files:
        print("No files with Uniclass prefix found.")
        return

    print("--- Mapping files for prefix removal ---")
    mapping = {}
    for f in files:
        # Match pattern like [Fi_10_10] filename.ext or [Fi_10_10] filename-Checklist.md
        name = f.name
        match = re.match(r"^\[Fi_\d+_\d+\]\s*(.*)$", name)
        if match:
            clean_name = match.group(1)
            mapping[name] = clean_name
            print(f"Mapped: {name} -> {clean_name}")
        else:
            print(f"Could not parse: {name}")

    # Read and update content of all markdown files in .md/
    print("\n--- Updating links inside markdown files ---")
    md_files = list(md_dir.glob("*.md"))
    for md_file in md_files:
        # Check if the file is one of the files being renamed (or already clean)
        content = md_file.read_text(encoding="utf-8")
        orig_content = content

        # Replace occurrences of old filenames
        for old_name, new_name in mapping.items():
            # Standard replace
            content = content.replace(old_name, new_name)

            # URL-encoded replace (e.g., %5BFi_10_10%5D%20... for markdown links)
            old_encoded = urllib.parse.quote(old_name)
            new_encoded = urllib.parse.quote(new_name)
            content = content.replace(old_encoded, new_encoded)

        if content != orig_content:
            md_file.write_text(content, encoding="utf-8")
            print(f"Updated links in: {md_file.name}")

    # Rename physical files
    print("\n--- Performing physical rename ---")
    for old_name, new_name in mapping.items():
        old_path = md_dir / old_name
        new_path = md_dir / new_name
        if old_path.exists():
            old_path.rename(new_path)
            print(f"Renamed: {old_name} -> {new_name}")

    print("\nSuccessfully removed Uniclass prefixes from filenames!")

if __name__ == "__main__":
    main()
