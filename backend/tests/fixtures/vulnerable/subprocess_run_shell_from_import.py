from subprocess import run


def run_command(command):
    run(command, shell=True)
