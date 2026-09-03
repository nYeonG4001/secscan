import os


class CustomFlask:
    class request:
        args = {"cmd": "echo test"}


flask = CustomFlask()


def handle_request():
    os.system(flask.request.args.get("cmd"))
