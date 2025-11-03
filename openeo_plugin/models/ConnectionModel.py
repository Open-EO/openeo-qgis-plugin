from base64 import b64encode, b64decode
import json

class ConnectionModel():
    def __init__(self, name, url):
        self.name = name
        self.url = url

    @classmethod
    def from_json(cls, json_string):
        # alternative constructor from json
        data = json.loads(json_string)

        name = b64decode(data["name"]).decode("utf-8")
        url = b64decode(data["url"]).decode("utf-8")
        
        return cls(name=name, url=url)

    def __repr__(self):
        return f"ConnectionModel('{self.name}','{self.url}')"
    
    def __str__(self):
        dict = {
            "name": b64encode(self.name.encode("utf-8")).decode("utf-8"),
            "url": b64encode(self.url.encode("utf-8")).decode("utf-8")
        }
        
        return json.dumps(dict)