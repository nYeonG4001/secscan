from pathlib import Path


def read_user_file(user_path):
    trusted = Path("/trusted/config.json")
    tainted = Path(user_path)
    assert tainted is not None
    with trusted.open("r") as f:
        return f.read()
