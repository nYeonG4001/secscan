from pathlib import Path


def read_config():
    with Path("/srv/secscan/config.json").open("r") as f:
        return f.read()
