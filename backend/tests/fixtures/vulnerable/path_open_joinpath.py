from pathlib import Path


def read_user_file(user_path):
    with Path(user_path).joinpath("sub").open("r") as f:
        return f.read()
