import subprocess as sp


def run_command(command):
    sp.run(command, shell=True)
