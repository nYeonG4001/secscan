import os

from flask import request


def handle_request():
    os.system(request.values.get("cmd"))
