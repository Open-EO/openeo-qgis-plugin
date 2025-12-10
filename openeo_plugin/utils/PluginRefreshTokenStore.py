from openeo.rest.auth.config import RefreshTokenStore

from qgis.core import QgsSettings

from ..models.CredentialsModel import CredentialsModel
from ..utils.settings import SettingsPath


class PluginRefreshTokenStore(RefreshTokenStore):
    def __init__(self, connectionId):
        super().__init__()
        self.id = connectionId

    def _getCredentials(self, empty_on_not_found=True):
        credentials = None
        settings = QgsSettings()
        logins = settings.value(SettingsPath.SAVED_LOGINS.value)
        for login in logins:
            if login["id"] == str(self.id):
                credentials = CredentialsModel.fromDict(login)
                return credentials
        if credentials is None:
            if empty_on_not_found:
                credentials = CredentialsModel(loginType="oidc", id=self.id)
                return credentials
            # this error was adapted from the original implementation
            # might require raising a different error because strictly
            # these are not files
            raise FileNotFoundError(self._path)

    def load(self, empty_on_not_found=True) -> dict:
        credentials = self._getCredentials(empty_on_not_found)
        try:
            if credentials is not None:
                if credentials.getTokenStore() is not None:
                    return credentials.getCredentials()
                else:
                    return {}
            else:
                return {}
        except Exception as e:
            raise RuntimeError(
                f"Failed to load {type(self).__name__}: {e!r}"
            ) from e

    def _write(self, data: dict):
        credentials = self._getCredentials()
        credentials.setTokenStore(data)

        # get saved credentials
        settings = QgsSettings()
        logins = settings.value(SettingsPath.SAVED_LOGINS.value)
        # update if exists,
        for i, login in enumerate(logins):
            if login.get("id") == self.id:
                logins[i] = credentials.toDict()
        # finally save the logins
        settings.setValue(SettingsPath.SAVED_LOGINS.value, logins)
