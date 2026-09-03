import pickle

from flask import request


def handle_request():
    pickle.Unpickler(request.get_json()["data"]).load()
