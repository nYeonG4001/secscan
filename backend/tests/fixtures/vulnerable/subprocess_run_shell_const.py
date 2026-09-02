import subprocess


def run_command(command):
    shell_flag = True
    subprocess.run(command, shell=shell_flag)
