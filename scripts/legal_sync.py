import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from ccba_legal import LegalSyncEngine
from ccba_legal.sync import GOOGLE_API_AVAILABLE, get_drive_service


def main():
    from scripts.legal.legal_sync import main as cli_main

    cli_main()


if __name__ == "__main__":
    main()
