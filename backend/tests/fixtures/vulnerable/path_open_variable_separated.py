from pathlib import Path


def read_user_file(user_path):
    p = Path(user_path)
    with p.open("r") as f:
        return f.read()
