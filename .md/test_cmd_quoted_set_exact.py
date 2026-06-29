import subprocess
import sys
import os
import pathlib

def test(tmp_path):
    sensitive_file = tmp_path / "secret_credential.txt"
    sensitive_file.write_text("cmd-quoted-secret")

    # Escaping double quotes inside cmd shell can be tricky. Let's try options:
    # Option 1: Just set X=sec without internal double quotes if possible, or escaping them.
    # Actually, Windows cmd set "X=sec" is equivalent to: set X=sec
    # If the user did: set "X=sec", the name is X, value is sec.
    # In python subprocess, if shell=True, it gets passed to cmd.exe /c.
    # Let's try:
    cmd_str = (
        'cmd.exe /c "set X=sec&& set Y=ret_cred&& set Z=ential.txt&& call type %X%%Y%%Z%"'
    )
    print("Command:", cmd_str)
    p = subprocess.Popen(
        cmd_str,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=tmp_path
    )
    stdout, stderr = p.communicate()
    print("STDOUT:", repr(stdout))
    print("STDERR:", repr(stderr))

if __name__ == "__main__":
    tmp = pathlib.Path("C:/Users/chuvu/AppData/Local/Temp/pytest-of-chuvu/pytest-187/test_cmd_quoted_set_bypass0")
    tmp.mkdir(parents=True, exist_ok=True)
    test(tmp)
