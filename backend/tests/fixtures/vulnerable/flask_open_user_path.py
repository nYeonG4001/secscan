from flask import request


def handle_request():
    with open(request.args.get("path"), "r") as f:
        return f.read()
