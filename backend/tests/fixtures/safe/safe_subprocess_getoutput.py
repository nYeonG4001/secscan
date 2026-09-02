import subprocess


def list_files():
    subprocess.getoutput("ls -la")
