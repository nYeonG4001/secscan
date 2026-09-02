import subprocess


def list_files():
    subprocess.getstatusoutput("ls -la")
