import subprocess


def run_command(command, shell_choice):
    subprocess.Popen(command, shell=shell_choice)
