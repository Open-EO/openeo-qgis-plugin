import json
import openeo
import uuid

class ConnectionModel():
    def __init__(self, name, url, id=None):
        self.name = name
        self.url = url
        if not id:
            self.id = uuid.uuid4()
        else:
            self.id = uuid.UUID(id)
    
    @classmethod
    def fromDict(cls, data):
        name = data["name"]
        url = data["url"]
        id = data["id"]

        return cls(name=name, url=url, id=id)
    
    def connect(self):
        return openeo.connect(self.url)

    def __str__(self):
        dict = self.toDict
        return json.dumps(dict)
    
    def toDict(self):
        dict = {
            "name": self.name,
            "url": self.url,
            "id": str(self.id)
        }
        return dict