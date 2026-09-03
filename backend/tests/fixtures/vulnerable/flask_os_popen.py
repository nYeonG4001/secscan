import os

from flask import request


def handle_request():
    os.popen(request.cookies["cmd"])
