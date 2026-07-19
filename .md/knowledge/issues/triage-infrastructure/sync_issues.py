import json
import subprocess
import os
import sys

def run_command(cmd):
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error executing command {' '.join(cmd)}: {e.stderr}", file=sys.stderr)
        return None

def main():
    repo = "vvChu/ccba-agent-platform"
    cmd = ["gh", "issue", "list", "--repo", repo, "--state", "all", "--limit", "100", 
           "--json", "number,title,state,labels,assignees,createdAt,updatedAt,body"]
    
    print(f"Executing: {' '.join(cmd)}")
    stdout = run_command(cmd)
    
    if stdout is None:
        print("Failed to fetch issues from GitHub CLI. Make sure 'gh' is installed and authenticated.")
        sys.exit(1)
        
    issues = json.loads(stdout)
    
    # Định nghĩa thư mục đích
    # Thư mục issues cục bộ
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Đi lên 1 cấp (thư mục issues/)
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
            "body": "Đây là issue mẫu được tạo tự động bởi script đồng bộ khi repo GitHub chưa có issue nào. Nhằm kiểm tra cấu trúc lưu trữ và hoạt động của Agent Triage."
        }
        issues.append(demo_issue)
        
    for issue in issues:
        num = issue.get("number", 0)
        title = issue.get("title", "")
        # GitHub issue state is OPEN/CLOSED, map to triage states or keep it simple
        gh_state = issue.get("state", "OPEN").lower()
        
        # Lấy mảng nhãn
        labels = [l.get("name") for l in issue.get("labels", [])]
        
        # Xác định trạng thái Triage cụ thể từ labels nếu có, nếu không thì map từ gh_state
        state = "needs-triage"
        for label in labels:
            if label in ["needs-triage", "needs-info", "ready-for-agent", "ready-for-human", "wontfix"]:
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
        
        frontmatter = f"""---
id: {num}
title: "{title}"
state: "{state}"
labels:
{chr(10).join([f'  - "{l}"' for l in labels])}
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
