class ConnectionModel():
    def __init__(self, name, url):
        self.name = name
        self.url = url

    def __repr__(self):
        return f"ConnectionModel('{self.name}','{self.url}')"
