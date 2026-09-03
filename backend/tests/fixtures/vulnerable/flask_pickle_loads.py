import pickle

from flask import request


def handle_request():
    pickle.loads(request.data)
