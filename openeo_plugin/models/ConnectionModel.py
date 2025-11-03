from base64 import b64encode, b64decode
import json

class ConnectionModel():
    def __init__(self, name, url):
        self.name = name
        self.url = url
    
    @classmethod
    def fromDict(cls, data):
        name = data["name"]
        url = data["url"]

        return cls(name=name, url=url)
    
    def __str__(self):
        dict = self.toDict
        return json.dumps(dict)
    
    def toDict(self):
        dict = {
            "name": self.name,
            "url": self.url
        }
        return dict