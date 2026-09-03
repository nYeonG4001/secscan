import pickle

from flask import request


def handle_request():
    pickle.load(request.get_data())
