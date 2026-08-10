import os, sys, re, urllib.parse
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
root = Path('.').resolve()
link_pattern = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')

broken_links = []
scanned_files = 0
total_links = 0

def is_relative_link(url):
    if url.startswith(('http://', 'https://', 'mailto:', 'ftp:', '#', 'file://')):
        return False
    if url.startswith('/'):
        return False
    return True

for target_dir in [root / '.agents' / 'skills', root / '.agents' / 'workflows']:
    for md_file in target_dir.rglob('*.md'):
        scanned_files += 1
        try:
            content = md_file.read_text(encoding='utf-8', errors='ignore')
        except Exception as e:
            continue
        
        # Remove code blocks to avoid false positives inside code blocks
        clean_content = re.sub(r'```.*?```', '', content, flags=re.DOTALL)

        for match in link_pattern.finditer(clean_content):
            link_text = match.group(1)
            link_target = match.group(2).strip()
            
            # Extract path part before fragment or query
            target_path_str = link_target.split('#')[0].split('?')[0]
            if not target_path_str or not is_relative_link(target_path_str):
                continue
            
            total_links += 1
            decoded_target = urllib.parse.unquote(target_path_str)
            target_path = (md_file.parent / decoded_target).resolve()
            
            if not target_path.exists():
                broken_links.append((str(md_file.relative_to(root)), link_text, link_target))

print(f"Scanned {scanned_files} markdown files in .agents/skills and .agents/workflows.")
print(f"Total relative links checked: {total_links}")
print(f"Broken relative links count: {len(broken_links)}")
if broken_links:
    print("Broken links detail:")
    for f, txt, tgt in broken_links:
        print(f"  File: {f} -> Text: '{txt}' Target: '{tgt}'")
