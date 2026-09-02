import pathlib


def read_config():
    with pathlib.Path("/srv/secscan/config.json").open("r") as f:
        return f.read()
