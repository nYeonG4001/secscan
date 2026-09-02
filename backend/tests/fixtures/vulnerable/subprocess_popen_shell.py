import subprocess


def run_command(command):
    subprocess.Popen(command, shell=True)
