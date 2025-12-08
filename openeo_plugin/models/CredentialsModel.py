import json


class CredentialsModel:
    def __init__(
        self,
        loginType,
        id=None,
        loginName=None,
        password=None,
        tokenStore={},
    ):
        self.id = id
        self.loginType = loginType
        self.loginName = loginName
        self.password = password
        self.tokenStore = tokenStore

    @classmethod
    def fromDict(cls, data):
        id = data["id"]
        loginType = data["loginType"]
        loginName = data["loginName"]
        password = data["password"]
        tokenStore = data["tokenStore"]

        return cls(loginType, id, loginName, password, tokenStore)

    def setId(self, id):
        id = str(id)
        self.id = id

    def setTokenStore(self, tokenStore):
        self.tokenStore = tokenStore

    def __str__(self):
        dict = self.toDict()
        return json.dumps(dict)

    def toDict(self):
        dict = {
            "loginType": self.loginType,
            "id": str(self.id),
            "loginName": self.loginName,
            "password": self.password,
            "tokenStore": self.tokenStore,
        }
        return dict
