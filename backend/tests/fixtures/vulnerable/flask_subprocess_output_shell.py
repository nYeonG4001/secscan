import subprocess

from flask import request


def handle_request():
    subprocess.getoutput(request.args.get("cmd"))
