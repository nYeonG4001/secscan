import os

from flask import request


def handle_request():
    _ = request.args.get("cmd")
    os.system("echo fixed_safe_command")
