import json
import os
import subprocess
import sys


def run_command(cmd: list[str]) -> str | None:
    """Execute a shell command and return its stdout.

    Args:
        cmd: List of command arguments.

    Returns:
        The command's stdout stripped of whitespace, or None if failed.
    """
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error executing {' '.join(cmd)}: {e.stderr}", file=sys.stderr)
        return None


def main() -> None:
    """Sync issues from GitHub to local Markdown files."""
    repo = "vvChu/ccba-agent-platform"
    cmd = [
        "gh",
        "issue",
        "list",
        "--repo",
        repo,
        "--state",
        "all",
        "--limit",
        "100",
        "--json",
        "number,title,state,labels,assignees,createdAt,updatedAt,body",
    ]

    print(f"Executing: {' '.join(cmd)}")
    stdout = run_command(cmd)

    if stdout is None:
        print(
            "Failed to fetch issues from GitHub CLI. Make sure 'gh' is installed and authenticated."
        )
        sys.exit(1)

    issues = json.loads(stdout)

    # Định nghĩa thư mục đích
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.abspath(os.path.join(script_dir, ".."))

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    print(f"Syncing issues to: {output_dir}")

    # Nếu không có issue nào trên GitHub, tạo một issue demo offline để minh họa
    if len(issues) == 0:
        print("No issues found on GitHub. Generating a offline demo issue...")
        demo_issue = {
            "number": 0,
            "title": "Offline Demo Issue - Triage Setup Check",
            "state": "OPEN",
            "labels": [{"name": "needs-triage"}, {"name": "documentation"}],
            "assignees": [],
            "createdAt": "2026-07-19T12:00:00Z",
            "updatedAt": "2026-07-19T12:00:00Z",
            "body": "Đây là issue mẫu được tạo tự động bởi script đồng bộ khi repo GitHub chưa có issue nào. Nhằm kiểm tra cấu trúc lưu trữ và hoạt động của Agent Triage.",
        }
        issues.append(demo_issue)

    for issue in issues:
        num = issue.get("number", 0)
        title = issue.get("title", "")
        # GitHub issue state is OPEN/CLOSED

        # Lấy mảng nhãn
        labels = [lbl.get("name") for lbl in issue.get("labels", [])]

        # Xác định trạng thái Triage cụ thể từ labels nếu có
        state = "needs-triage"
        for label in labels:
            if label in [
                "needs-triage",
                "needs-info",
                "ready-for-agent",
                "ready-for-human",
                "wontfix",
            ]:
                state = label
                break

        assignees = issue.get("assignees", [])
        assignee = assignees[0].get("login") if assignees else "none"

        created_at = issue.get("createdAt", "")
        updated_at = issue.get("updatedAt", "")
        body = issue.get("body", "")

        # Định nghĩa tên file: issue-<num>.md
        filename = f"issue-{num}.md"
        filepath = os.path.join(output_dir, filename)

        joined_labels = "\n".join([f'  - "{lbl_item}"' for lbl_item in labels])
        frontmatter = f"""---
id: {num}
title: "{title}"
state: "{state}"
labels:
{joined_labels}
assignee: "{assignee}"
created_at: "{created_at}"
updated_at: "{updated_at}"
---

# 📖 Mô tả (Description)
{body}

---

# 💬 Thảo luận (Discussion Log)
*(Chưa có thảo luận)*
"""
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(frontmatter)

        print(f"Synced {filename}")


if __name__ == "__main__":
    main()
