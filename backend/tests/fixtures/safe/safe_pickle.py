import pickle


def load_trusted():
    trusted_bytes = pickle.dumps({"key": "value"})
    pickle.loads(trusted_bytes)
