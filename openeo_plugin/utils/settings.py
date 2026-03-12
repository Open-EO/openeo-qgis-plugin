from enum import Enum
import platform


class SettingsPath(Enum):
    SAVED_CONNECTIONS = "openeo_plugin/saved_connections"
    SAVED_LOGINS = "openeo_plugin/saved_logins"
    PLUGIN_VERSION = "openeo_plugin/version"


def getOs():
    osType = platform.system().lower()
    if osType == "linux":
        distro = platform.freedesktop_os_release()["ID"]
        return distro
    return osType
