import os

from flask import request


def handle_request():
    command = request.args.get("cmd")
    os.system(command)
