import os

from flask import request


def handle_request(user_param):
    os.system(user_param + request.args.get("cmd"))
