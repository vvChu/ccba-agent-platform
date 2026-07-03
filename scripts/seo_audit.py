#!/usr/bin/env python3
"""
SEO Audit Tool for ccba-agent-platform.
CLI wrapper delegating core logic to ccba_ai.services.seo.
"""

import argparse
import sys
from pathlib import Path

from ccba_ai.services import seo

# Enforce UTF-8 output
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="CCBA Technical SEO Auditor CLI")
    parser.add_argument("file", help="Path to the file to audit (Markdown or HTML)")
    args = parser.parse_args()

    file_path = Path(args.file)
    print(f"\n[SEO Auditor] Auditing file: \x1b[36m{file_path.name}\x1b[0m\n")

    try:
        result = seo.audit_file(file_path)

        score = result["score"]
        if score >= 90:
            color = "\x1b[32m"  # Green
        elif score >= 70:
            color = "\x1b[33m"  # Yellow
        else:
            color = "\x1b[31m"  # Red

        print(f"Overall SEO Score: {color}{score}/100\x1b[0m")
        print("-" * 50)
        print("Checked Metrics:")
        for c in result["checks"]:
            print(f"  - {c}")
        print("-" * 50)

        if result["issues"]:
            print("Issues found:")
            for idx, issue in enumerate(result["issues"], 1):
                print(f"  {idx}. \x1b[33m[Warning]\x1b[0m {issue}")
        else:
            print("\x1b[32mCongratulations! No SEO issues found in this file.\x1b[0m")
        print()
        sys.exit(0)

    except Exception as e:
        print(f"\x1b[31m[Error]\x1b[0m {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
