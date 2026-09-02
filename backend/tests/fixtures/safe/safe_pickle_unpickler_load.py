import io
import pickle


def load_trusted():
    trusted_bytes = pickle.dumps({"key": "value"})
    pickle.Unpickler(io.BytesIO(trusted_bytes)).load()
