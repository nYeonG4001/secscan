import subprocess


def run_command(command):
    subprocess.check_output(command, shell=True)
