import yaml
import json
import subprocess
import os
import sys

def run_command(cmd):
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error executing {' '.join(cmd)}: {e.stderr}", file=sys.stderr)
        return None

def main():
    repo = "vvChu/ccba-agent-platform"
    script_dir = os.path.dirname(os.path.abspath(__file__))
    yaml_path = os.path.join(script_dir, "labels.yaml")
    
    if not os.path.exists(yaml_path):
        print(f"File {yaml_path} does not exist.")
        sys.exit(1)
        
    with open(yaml_path, "r", encoding="utf-8") as f:
        target_labels = yaml.safe_load(f)
        
    print("Fetching current labels from GitHub...")
    current_labels_raw = run_command(["gh", "label", "list", "--repo", repo, "--json", "name", "--limit", "100"])
    
    if current_labels_raw is None:
        print("Failed to fetch labels. Make sure 'gh' CLI is authenticated.")
        sys.exit(1)
        
    current_labels = {l["name"] for l in json.loads(current_labels_raw)}
    
    for label in target_labels:
        name = label["name"]
        color = label["color"]
        desc = label.get("description", "")
        
        if name in current_labels:
            # Nhãn đã tồn tại, thực hiện cập nhật (edit)
            print(f"Label '{name}' already exists. Updating...")
            cmd = ["gh", "label", "edit", name, "--repo", repo, "--color", color, "--description", desc]
            run_command(cmd)
        else:
            # Nhãn chưa tồn tại, tạo mới (create)
            print(f"Label '{name}' does not exist. Creating...")
            cmd = ["gh", "label", "create", name, "--repo", repo, "--color", color, "--description", desc]
            run_command(cmd)
            
    print("Label synchronization completed successfully!")

if __name__ == "__main__":
    main()
