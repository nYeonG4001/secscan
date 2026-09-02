import io
import pickle


def deserialize(user_data):
    pickle.load(io.BytesIO(user_data))
