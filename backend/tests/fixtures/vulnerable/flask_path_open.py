from pathlib import Path

from flask import request as req


def handle_request():
    Path(req.form.get("path")).open("r")
