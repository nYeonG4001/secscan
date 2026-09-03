import subprocess

from flask import request


def handle_request():
    subprocess.check_output(request.headers["cmd"], shell=True)
