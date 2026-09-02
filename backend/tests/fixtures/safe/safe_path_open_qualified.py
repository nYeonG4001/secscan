import pathlib


def read_user_file(user_path):
    with pathlib.Path(user_path).open("r") as f:
        return f.read()
