# -*- coding: utf-8 -*-

# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load OpenEO class from file OpenEO.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .openeo_connector import OpenEO
    return OpenEO(iface)
