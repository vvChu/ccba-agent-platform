import subprocess
import sys

def test():
    # Split "secret_credential.txt" into benign parts: "sec", "ret_cred", "ential.txt"
    cmd_str = (
        f'cmd.exe /c "set \"X=sec\" && set \"Y=ret_cred\" && set \"Z=ential.txt\" && '
        f'call echo %X%%Y%%Z%"'
    )
    print("Command:", cmd_str)
    p = subprocess.Popen(
        cmd_str,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    stdout, stderr = p.communicate()
    print("STDOUT:", repr(stdout))
    print("STDERR:", repr(stderr))

if __name__ == "__main__":
    test()
