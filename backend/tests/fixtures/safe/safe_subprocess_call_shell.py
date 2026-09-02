import subprocess


def run_command(command):
    subprocess.call(command, shell=False)
