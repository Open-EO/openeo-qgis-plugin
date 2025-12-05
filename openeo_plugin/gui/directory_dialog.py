from qgis.PyQt.QtWidgets import QFileDialog


class DirectoryDialog(QFileDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFileMode(self.FileMode.Directory)
        self.setAcceptMode(self.AcceptMode.AcceptOpen)
        self.setWindowTitle("Download Results to...")

    def selectDirectory(self):
        result = self.exec()
        dir = None
        if result:
            dir = self.selectedUrls()[0]
            if dir.isLocalFile() or dir.isEmpty():
                dir = dir.toLocalFile()
            else:
                dir = dir.toString()
        return dir
