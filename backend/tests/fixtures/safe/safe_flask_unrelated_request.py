import os


class CustomRequest:
    def __init__(self):
        self.args = {"cmd": "echo test"}


request = CustomRequest()


def handle_request():
    os.system(request.args.get("cmd"))
