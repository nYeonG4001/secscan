import subprocess


def run_command(command, shell_choice):
    subprocess.check_call(command, shell=shell_choice)
