import json


class CredentialsModel:
    def __init__(
        self,
        loginType,
        id=None,
        username=None,
        password=None,
        tokens={},
    ):
        self.id = id
        self.loginType = loginType
        self.credentials = {}

        if self.loginType == "oidc":
            self.credentials = tokens
        elif self.loginType == "basic":
            self.credentials = {
                "username": username,
                "password": password,
            }

    @classmethod
    def fromDict(cls, data):
        id = data["id"]
        loginType = data["loginType"]
        username = None
        password = None
        tokens = None
        if loginType == "oidc":
            tokens = data["credentials"]

        if loginType == "basic":
            username = data["credentials"]["username"]
            password = data["credentials"]["password"]

        return cls(loginType, id, username, password, tokens)

    def setId(self, id):
        id = str(id)
        self.id = id

    def setTokenStore(self, tokens):
        if self.loginType == "oidc":
            self.setCredentials(tokens)
            return True
        else:
            return False

    def getTokenStore(self):
        if self.loginType == "oidc":
            return self.getCredentials()
        return None

    def setCredentials(self, creds):
        self.credentials = creds

    def getCredentials(self):
        return self.credentials

    def __str__(self):
        dict = self.toDict()
        return json.dumps(dict)

    def toDict(self):
        dict = {
            "loginType": self.loginType,
            "id": str(self.id),
            "credentials": self.credentials,
        }
        return dict
