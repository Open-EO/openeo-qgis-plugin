from qgis.core import QgsTask
from qgis.PyQt.QtCore import pyqtSignal


class DownloadAssetTask(QgsTask):
    """Custom task for downloading assets with GUI-safe signals"""

    # Custom signals to communicate with the main thread
    download_complete = pyqtSignal(str, str)  # assetName, dir
    download_error = pyqtSignal(
        str, str, Exception
    )  # assetName, dir, exception

    def __init__(self, description, download_func, dir):
        super().__init__(description, QgsTask.CanCancel)
        self.download_func = download_func
        self.dir = dir
        self.exception = None

    def run(self):
        """Execute the download in the background thread"""
        try:
            self.download_func(dir=self.dir)
            return True
        except Exception as e:
            self.exception = e
            return False

    def finished(self, result):
        """Called when task finishes - runs on main thread"""
        pass


class DownloadJobAssetsTask(QgsTask):
    """Custom task for downloading job assets with GUI-safe signals"""

    def __init__(self, description, job_item, dir):
        super().__init__(description, QgsTask.CanCancel)
        self.job_item = job_item
        self.dir = dir
        self.errors = 0
        self.total_assets = 0
        self.exception = None
        self.canceled = False

    def run(self):
        """Execute the download in the background thread"""
        try:
            self.job_item.populateAssetItems()
            self.total_assets = len(self.job_item.assetItems)

            for i, asset in enumerate(self.job_item.assetItems):
                if self.isCanceled():
                    self.canceled = True
                    return False
                try:
                    progress = int((i / self.total_assets) * 100)
                    self.setProgress(progress)
                    asset.downloadAsset(dir=self.dir)
                except Exception as e:
                    self.errors += 1
                    # Store first exception for error reporting
                    if self.exception is None:
                        self.exception = e
            return True
        except Exception as e:
            self.exception = e
            return False

    def finished(self, result):
        """Called when task finishes - runs on main thread"""
        pass
