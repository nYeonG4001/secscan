from pathlib import Path


def read_user_file(user_path):
    with Path(user_path).open("r") as f:
        return f.read()
