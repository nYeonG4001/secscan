import pickle


def load_from_user_path(user_path):
    f = open(user_path, "rb")
    pickle.load(f)
