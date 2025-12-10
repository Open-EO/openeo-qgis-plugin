from qgis.core import QgsSettings

from ..utils.settings import SettingsPath


class CredentialsModel:
    def __init__(self, id, loginType, credentials={}):
        if loginType not in ["basic", "oidc"]:
            raise ValueError(f"Unsupported login type: {loginType}")

        self.id = id
        self.loginType = loginType
        self.credentials = credentials

    @classmethod
    def fromBasic(cls, id, username, password):
        return cls(id, "basic", {"username": username, "password": password})

    @classmethod
    def fromOIDC(cls, id, tokens):
        return cls(id, "oidc", tokens)

    @classmethod
    def fromStore(cls, data, version=None):
        loginType = data.get("loginType")
        id = data.get("id")
        if version == "2.0-beta.2":
            match loginType:
                case "basic":
                    return cls.fromBasic(
                        id, data.get("username"), data.get("password")
                    )
                case _:
                    # Nothing stored, potentially came from openeo-python-client
                    return None
        else:
            return cls(id, loginType, data.get("credentials"))

    def isExpired(self):
        # todo: for OIDC check expiry of JWT
        return False

    def __str__(self):
        return f"<CredentialsModel type={self.loginType} id={self.id}>"

    def toDict(self):
        return {
            "loginType": self.loginType,
            "id": str(self.id),
            "credentials": self.credentials,
        }


class Credentials:
    def __init__(self):
        self.settings = QgsSettings()
        self.key = SettingsPath.SAVED_LOGINS.value

    def get(self, id: str) -> CredentialsModel | None:
        logins = self.settings.value(self.key)
        for login in logins:
            if login["id"] == str(id):
                return CredentialsModel.fromStore(login)
        return None

    def _load(self) -> list[dict]:
        return self.settings.value(self.key) or []

    def update(self, version):
        logins = self._load()
        new_logins = []
        for login in logins:
            credentials = CredentialsModel.fromStore(login, version)
            if credentials and not credentials.isExpired():
                new_logins.append(login)

        self.settings.setValue(self.key, new_logins)

    def remove(self, id):
        logins = self._load()
        new_logins = []
        for login in logins:
            if login["id"] != str(id):
                new_logins.append(login)

        self.settings.setValue(self.key, new_logins)

    def add(self, credential: CredentialsModel):
        self.remove(credential.id)

        logins = self._load()
        logins.append(credential.toDict())
        self.settings.setValue(self.key, logins)

    def clear(self):
        self.settings.setValue(self.key, [])
