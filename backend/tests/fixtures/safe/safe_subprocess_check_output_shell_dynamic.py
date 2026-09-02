import subprocess


def run_command(command, shell_choice):
    subprocess.check_output(command, shell=shell_choice)
