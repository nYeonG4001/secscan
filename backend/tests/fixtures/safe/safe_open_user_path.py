def read_server_config():
    with open("/srv/secscan/config.json", "r", encoding="utf-8") as source:
        return source.read()
