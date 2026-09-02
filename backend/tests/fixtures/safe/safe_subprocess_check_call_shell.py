import subprocess


def run_command(command):
    subprocess.check_call(command, shell=False)
