from openeo.rest.auth.config import RefreshTokenStore

from ..models.CredentialsModel import CredentialsModel, Credentials


class PluginRefreshTokenStore(RefreshTokenStore):
    def __init__(self, connectionId):
        super().__init__()
        self.id = str(connectionId)
        self.manager = Credentials()

    def get_refresh_token(self, issuer: str, client_id: str):
        model = self.manager.get(self.id)
        creds = model.credentials if model else {}
        if (
            creds.get("issuer") == issuer
            and creds.get("client_id") == client_id
        ):
            return creds.get("refresh_token", None)
        else:
            return None

    def set_refresh_token(
        self, issuer: str, client_id: str, refresh_token: str
    ):
        credentials = {
            "issuer": issuer,
            "client_id": client_id,
            "refresh_token": refresh_token,
        }
        self.manager.add(CredentialsModel.fromOIDC(self.id, credentials))
