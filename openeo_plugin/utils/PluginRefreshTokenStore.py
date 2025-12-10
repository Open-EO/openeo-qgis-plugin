from openeo.rest.auth.config import RefreshTokenStore

from ..models.CredentialsModel import CredentialsModel, Credentials


class PluginRefreshTokenStore(RefreshTokenStore):
    def __init__(self, connectionId):
        super().__init__()
        self.id = str(connectionId)
        self.manager = Credentials()

    def get_refresh_token(self, issuer: str, client_id: str):
        key = issuer + "|" + client_id
        model = self.manager.get(self.id)
        if model:
            return model.credentials.get(key, None)
        else:
            return None

    def set_refresh_token(
        self, issuer: str, client_id: str, refresh_token: str
    ):
        key = issuer + "|" + client_id
        credentials = {key: refresh_token}
        self.manager.add(CredentialsModel.fromOIDC(self.id, credentials))
