"""Script to execute Ticket 02: Migrating and restructuring OKF Bundles into Knowledge Spoke."""

import shutil
import sys
from pathlib import Path



def migrate_data():
    hub_base = Path("d:/GitHubProjects/ccba-agent-platform/.md/legal_docs")
    spoke_base = Path("D:/GitHubProjects/ccba-legal-knowledge/legal_docs/REGULATION_QCVN")

    print("[Ticket 02] Migrating OKF Bundles to Spoke...")

    # 1. Migrate QCVN 04
    src_q04 = hub_base / "qcvn_04_2021_bxd"
    dst_q04 = spoke_base / "qcvn_04_2021_bxd"
    if src_q04.exists():
        if dst_q04.exists():
            shutil.rmtree(dst_q04)
        shutil.copytree(src_q04, dst_q04)
        print(" ✅ Migrated QCVN 04 OKF Bundle to Spoke")

    # 2. Migrate QCVN 06
    src_q06 = hub_base / "qcvn_06_2022_bxd"
    dst_q06 = spoke_base / "qcvn_06_2022_bxd"
    if src_q06.exists():
        if dst_q06.exists():
            shutil.rmtree(dst_q06)
        shutil.copytree(src_q06, dst_q06)
        print(" ✅ Migrated QCVN 06 OKF Bundle to Spoke")

    # Audit files in Spoke
    spoke_files = list(Path("D:/GitHubProjects/ccba-legal-knowledge/legal_docs").glob("**/*"))
    spoke_files = [f for f in spoke_files if f.is_file()]
    print(f"\nTotal files in Knowledge Spoke legal_docs: {len(spoke_files)}")
    for f in sorted(spoke_files):
        rel = f.relative_to(Path("D:/GitHubProjects/ccba-legal-knowledge"))
        print(f" - {rel}")


if __name__ == "__main__":
    if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    migrate_data()

