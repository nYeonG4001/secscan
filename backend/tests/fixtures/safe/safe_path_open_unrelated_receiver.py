class Connection:
    def open(self, mode):
        raise NotImplementedError


def get_connection(resource_path):
    return Connection()


def read_user_file(user_path):
    conn = get_connection(user_path)
    with conn.open("r") as f:
        return f.read()
