import ctypes
import os
import subprocess
import sys
from ccba_legal.harness import HarnessGuard

# 1. Pre-load ctypes kernel32 before entering guard
kernel32 = ctypes.windll.kernel32

# Define constants
GENERIC_WRITE = 0x40000000
CREATE_ALWAYS = 2
FILE_ATTRIBUTE_NORMAL = 0x80

def test_bypass():
    print("Starting bypass test...")
    # Clean up from previous run if any
    if os.path.exists("temp_bypass_exec.py"):
        os.remove("temp_bypass_exec.py")
    
    with HarnessGuard():
        # 2. Write file using raw OS handle via pre-loaded ctypes
        handle = kernel32.CreateFileW(
            "temp_bypass_exec.py",
            GENERIC_WRITE,
            0,
            None,
            CREATE_ALWAYS,
            FILE_ATTRIBUTE_NORMAL,
            None
        )
        if handle == -1:
            raise RuntimeError("Failed to create file via ctypes")
            
        data = b"print('Bypass Succeeded! Read .env:', open('.env').read())"
        written = ctypes.c_ulong(0)
        res = kernel32.WriteFile(
            handle,
            data,
            len(data),
            ctypes.byref(written),
            None
        )
        kernel32.CloseHandle(handle)
        
        if not res:
            raise RuntimeError("Failed to write to file via ctypes")

        # 3. Execute the written file
        # Since temp_bypass_exec.py was not written via Python open hooks, 
        # it is not in _written_files and should execute without PermissionError.
        try:
            print("Attempting to run the written file...")
            subprocess.run([sys.executable, "temp_bypass_exec.py"], check=True)
            print("SUCCESS: Bypass worked! The file executed despite HarnessGuard.")
        except PermissionError as e:
            print("FAILED: PermissionError raised as expected:", e)
        except Exception as e:
            print("FAILED: Unexpected error:", e)

    # Clean up
    if os.path.exists("temp_bypass_exec.py"):
        os.remove("temp_bypass_exec.py")

if __name__ == "__main__":
    test_bypass()
