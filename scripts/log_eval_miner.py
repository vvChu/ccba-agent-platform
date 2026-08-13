import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from scripts.eval.log_eval_miner import main, mine_logs_and_export  # noqa: F401

if __name__ == "__main__":
    sys.exit(main())
