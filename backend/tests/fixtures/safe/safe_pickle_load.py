import io
import pickle


def load_trusted():
    trusted_bytes = pickle.dumps({"key": "value"})
    pickle.load(io.BytesIO(trusted_bytes))
