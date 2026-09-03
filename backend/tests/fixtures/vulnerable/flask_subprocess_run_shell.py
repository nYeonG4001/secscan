import subprocess

import flask


def handle_request():
    subprocess.run(flask.request.json["cmd"], shell=True)
