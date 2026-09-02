from pathlib import Path as SafePath


def read_user_file(user_path):
    with SafePath(user_path).open("r") as f:
        return f.read()
