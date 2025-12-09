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
        loginName = None
        password = None
        tokenStore = None
        if loginType == "oidc":
            tokenStore = data["credentials"]

        if loginType == "basic":
            loginName = data["credentials"]["username"]
            password = data["credentials"]["password"]

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
        credentials = {}
        if self.loginType == "oidc":
            credentials = self.tokenStore
        elif self.loginType == "basic":
            credentials = {
                "username": self.loginName,
                "password": self.password,
            }

        dict = {
            "loginType": self.loginType,
            "id": str(self.id),
            "credentials": credentials,
        }
        return dict
