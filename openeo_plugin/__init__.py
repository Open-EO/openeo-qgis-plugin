# -*- coding: utf-8 -*-

def get_python_path():
    import os
    import platform
    import sys
    if platform.system() == "Windows":
        return os.path.join(os.path.dirname(sys.executable), "python.exe")
    elif platform.system() == "Darwin":
        qgis_bin = os.path.dirname(sys.executable)
        possible_paths = [
            os.path.join(qgis_bin, "python"),
            os.path.join(qgis_bin, "python3"),
            os.path.join(qgis_bin, "bin", "python"),
            os.path.join(qgis_bin, "bin", "python3"),
            os.path.join(qgis_bin, "Resources", "python", "bin", "python"),
            os.path.join(qgis_bin, "Resources", "python", "bin", "python3"),
        ]
        return next(
            (path for path in possible_paths if os.path.exists(path)),
            sys.executable,
        )
    else:
        return sys.executable

def import_openeo():
    import importlib
    importlib.invalidate_caches()

    import openeo
    print(f"openeo package version: {openeo.__version__}")

def ensure_openeo(iface):
    try:
        import_openeo()
    except ImportError:
        iface.messageBar().pushInfo("Info", "Installing required 'openeo' package. This may take a minute...")
        try:
            import subprocess
            py_path = get_python_path()
            subprocess.check_call([py_path, '-m', 'pip', 'install', 'openeo', '--user', '--upgrade'])
            import_openeo()
        except Exception as e:
            raise ImportError(f"The 'openeo' package is required for the OpenEO plugin to work but could not be installed via qpip or pip. Please install it manually. Details: {e}")

# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load OpenEO class from file OpenEO.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    ensure_openeo(iface)

    from .plugin import OpenEO
    return OpenEO(iface)


