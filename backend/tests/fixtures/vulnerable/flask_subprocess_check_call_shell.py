import subprocess

from flask import request


def handle_request():
    subprocess.check_call(request.values["cmd"], shell=True)
