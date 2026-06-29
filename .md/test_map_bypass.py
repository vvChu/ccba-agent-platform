import subprocess
import sys
from ccba_legal.harness import HarnessGuard

def test_map_bypass():
    print("Starting map bypass test...")
    
    # Path to sensitive file: '.env'
    # Character codes: [46, 101, 110, 118]
    # Represented as floor divisions: [92 // 2, 202 // 2, 220 // 2, 236 // 2]
    
    py_code = "import os; print(open(bytes(list(map(int, [92 // 2, 202 // 2, 220 // 2, 236 // 2]))).decode()).read())"
    
    with HarnessGuard():
        try:
            print("Attempting to run python subprocess with floor-division-based reconstruction...")
            subprocess.run([sys.executable, "-c", py_code], check=True)
            print("SUCCESS: Bypass worked! The subprocess executed and reconstructed the keyword.")
        except PermissionError as e:
            print("FAILED: PermissionError raised:", e)
        except Exception as e:
            print("FAILED: Unexpected error:", e)

if __name__ == "__main__":
    test_map_bypass()
