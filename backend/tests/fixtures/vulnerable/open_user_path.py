async def read_user_file(path):
    with open(path, "r", encoding="utf-8") as source:
        return source.read()
