import pickle


def deserialize(user_data):
    pickle.Unpickler(user_data).load()
