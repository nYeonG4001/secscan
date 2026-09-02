import subprocess


def run_command(command, shell_choice):
    subprocess.call(command, shell=shell_choice)
