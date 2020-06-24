# -*- coding: utf-8 -*-
"""
/***************************************************************************
 OpenEODialog
    This class is the main dialog of the plugin giving the possibility to explore the backend,
    handle jobs and handle services.
                             -------------------
        begin                : 2019-07-18
        git sha              : $Format:%H$
        copyright            : (C) 2019 by Bernhard Goesswein
        email                : bernhard.goesswein@geo.tuwien.ac.at
 ***************************************************************************/
/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
########################################################################################################################
########################################################################################################################

import os
import json
import webbrowser
import copy
import time, threading
from hashlib import md5

from qgis.PyQt import uic, QtGui, QtWidgets
from qgis.PyQt.QtWidgets import QTreeWidgetItem, QTableWidgetItem, QMessageBox
import qgis.PyQt.QtCore as QtCore
from qgis.core import QgsRasterLayer, QgsProject, QgsTask, QgsApplication, QgsMessageLog
from qgis.utils import iface

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QPushButton, QHBoxLayout, QTextEdit, QListWidget, QListWidgetItem, QApplication, \
    QLabel, QGridLayout, QVBoxLayout, QDialog, QLineEdit

from PyQt5.QtCore import Qt, QSize, QSettings, QTimer
from PyQt5.QtGui import QColor, QIcon, QPixmap

from .models.result import Result
from .models.processgraph import Processgraph
from .models.openeohub import get_hub_jobs
from .utils.logging import info, warning, error
from .models.models import Job, Process, Service

from .job_detail_dialog import JobDetailDialog
from .job_adapt_dialog import JobAdaptDialog
from .service_create_dialog import ServiceCreateDialog

os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)  # enable highdpi scaling
QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)  # use highdpi icons

########################################################################################################################
########################################################################################################################

# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'openeo_connector_dialog_base.ui'))


class OpenEODialog(QtWidgets.QDialog, FORM_CLASS):
    """
    This class is the main dialog of the plugin giving the possibility to explore the backend,
    handle jobs and handle services.
    """
    def __init__(self, parent=None, interface=None, backend=None):
        """
        Constructor method: Initializing the button behaviours and the Table entries.
        :param parent: parent dialog of this dialog (e.g. OpenEODialog).
        :param interface: Interface to show the dialog.
        :param backend: Backend: Currently connected backend.
        """
        super(OpenEODialog, self).__init__(parent)

        QApplication.setStyle("cleanlooks")

        self.jobs_hash = ""
        self.iface = interface
        self.processgraph = Processgraph()
        self.called = False
        self.called2 = False
        self.processes = None
        self.services_table = {}
        self.jobs_table = {}

        self.setupUi(self)

        self.operationManualBtn.clicked.connect(self.user_manual)
        self.operationManualBtn.hide()

        self.collectionBox.currentTextChanged.connect(self.col_info)

        self.collectionBox.setEnabled(True)
        self.collectionBox.show()
        self.label_12.hide()

        self.processBox.currentTextChanged.connect(self.process_selected)
        self.refreshButton.clicked.connect(self.refresh_jobs)
        self.refreshButton_service.clicked.connect(self.refresh_services)

        self.refreshButton.setEnabled(True)
        self.refreshButton_service.setEnabled(True)

        # Set initial button visibility correctly
        self.all_bands = []
        self.limit_west = -100000000000000000
        self.limit_east = 100000000000000000
        self.limit_north = 100000000000000000
        self.limit_south = -100000000000000000

        # Link to the Web Editor Demo Version:
        self.moveButton.clicked.connect(self.web_view)

        self.infoBtn2.clicked.connect(self.pr_info)
        self.infoBtn2.setEnabled(True)

        # Bands
        self.label_16.hide()
        self.label_16.setEnabled(False)

        # Adapt Job from Hub
        self.loadHubBtn.clicked.connect(self.show_jobs_from_hub_dialog)

        # Create Job
        self.createjobBtn.clicked.connect(self.create_job)
        self.createserviceBtn.clicked.connect(self.create_service)
        self.servicewebBtn.clicked.connect(self.web_view)

        # Jobs Tab
        self.init_jobs()
        self.init_services()

        self.tab_3.setEnabled(False)

        self.backend = copy.deepcopy(backend)

        collection_result = self.backend.get_collections()

        self.infoBtn2.setVisible(True)

        self.collectionBox.clear()
        self.processBox.clear()

        # Load Collections from Backend
        self.collectionBox.addItem("Choose one of the data sets listed below")
        for col in collection_result:
            if "id" in col:
                self.collectionBox.addItem(col['id'])

        # Load Processes from Backend
        self.processBox.addItem("Select a process")
        for key, val in self.backend.get_processes().items():
            self.processBox.addItem(key)

        self.refresh_jobs()
        self.refresh_services()

        if len(collection_result) == 0 and len(self.backend.get_processes()) == 0:
            warning(self.iface, "Backend URL does not have collections or processes defined, or is not valid!")
            return

        self.tab_3.setEnabled(True)

        self.backend_info()

        self.dlg = None

        # Load from openEO Hub
        self.example_hub_jobs = None
        self.hub_jobs_window = None
        self.exampleJobBox = None

        # User Manual
        self.umWindow = None

        # Explore Backend
        self.infoWindow2 = None

        self.infoWindow5 = None

        # Start autorefreshing thread
        # self.task1 = TestTask('Scheduled Task', self.iface)
        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh_task)
        self.timer.start(3000)
        # QgsMessageLog.logMessage("Start Timer!", "name")

    def closeEvent(self, event):
        self.timer.stop()

    def refresh_task(self):
        if self.tabWidget.currentIndex() == 1:
            self.refresh_jobs()
        elif self.tabWidget.currentIndex() == 2:
            self.refresh_services()

    def web_view(self):
        """
        Opens the web browser and the openEO web editor with the currently connected backend.
        """
        try:
            webbrowser.open("https://editor.openeo.org/?server={}".format(self.backend.url))
        except:
            pass
        # QWebEngineView, QWebView...

    def web_view_close(self):
        """
        Opens the web browser and the openEO web editor with the currently connected backend.
        """
        self.webWindow.close()
        return

    def show_jobs_from_hub_dialog(self):
        """
        Opens an new dialog to select available jobs from the openEO Hub.
        The user can then select one of them and adapt them or create a job out of them.
        """
        self.example_hub_jobs = get_hub_jobs()

        # Open a window, where desired job can be selected
        self.hub_jobs_window = QDialog(parent=self)
        hbox6 = QHBoxLayout()
        self.exampleJobBox = QListWidget()
        for job in self.example_hub_jobs:
            job_item = QListWidgetItem(self.exampleJobBox)
            job_item.setFlags(
                job_item.flags() | QtCore.Qt.ItemIsSelectable)  # only one item can be selected this time
            job_item.setSelected(False)
            job_item.setText(job.title)  # add Titles as QListWidgetItems

        self.exampleJobBox.setMinimumWidth(500)

        close_window_btn = QPushButton('Show process graph \n and close window')
        hbox6.addWidget(self.exampleJobBox)
        hbox6.addWidget(close_window_btn)
        close_window_btn.clicked.connect(self.pick_job_from_hub)
        self.hub_jobs_window.setLayout(hbox6)
        self.hub_jobs_window.setWindowTitle('Select a Job')
        self.hub_jobs_window.show()

    def pick_job_from_hub(self):
        """
        Opens a job adaption dialog with the selected openEO Hub job.
        """
        selected_row = self.exampleJobBox.currentRow()
        self.hub_jobs_window.close()

        job = self.example_hub_jobs[selected_row].to_job()

        self.dlg = JobAdaptDialog(iface=self.iface, job=job, backend=self.backend, main_dia=self)
        self.dlg.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.dlg.show()

    def create_job(self):
        """
        Creates a new job to get adapted by a new dialog window.
        """
        job = Job()
        process = Process()
        process.process_graph = {"load_collection1": {"process_id": "load_collection", "arguments": {}}}

        job.process = process

        self.dlg = JobAdaptDialog(iface=self.iface, job=job, backend=self.backend, main_dia=self)
        self.dlg.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.dlg.show()

    def create_service(self):
        """
        Creates a new service from job by a new dialog window.
        """
        self.dlg = ServiceCreateDialog(iface=self.iface, backend=self.backend)
        self.dlg.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.dlg.show()

    def user_manual(self):
        """
        Shows the user manual window.
        """
        self.umWindow = QDialog(parent=self)

        # User Manual Text
        text = QLabel()
        user_manual_text = open(os.path.join(os.path.dirname(__file__), './user_manual_text.txt')).read()
        text.setText(str(user_manual_text))
        # Title
        title = QLabel()
        title.setText("User Manual \n ")
        start_text = QLabel()
        start_text.setText("1. At first, please focus on the upper part (header) of the openEO Plugin. "
                           "There, you can choose a back-end and enter your login credentials. \nBy clicking "
                           "the “Connect”-Button, you will be connected with the chosen back-end. \nIf the connection "
                           "was successful you will see it in the Status text. \n")
        # openEO Header Image
        image = QLabel()
        image.setPixmap(QPixmap(os.path.join(os.path.dirname(__file__), 'images/openEO_plugin_header.png')))

        grid = QGridLayout()
        grid.setSpacing(4)
        grid.addWidget(title, 0, 0)
        grid.addWidget(start_text, 1, 0)
        grid.addWidget(image, 2, 0)
        grid.addWidget(text, 4, 0)
        self.umWindow.setLayout(grid)
        self.umWindow.setWindowTitle('User Manual')
        self.umWindow.show()

    def col_info(self):
        """
        Loads the collection info into the collection info text field.
        """
        collection_info_result = self.backend.get_collections()
        selected_col = str(self.collectionBox.currentText())
        for col_info in collection_info_result:
            if str(col_info['id']) == selected_col:
                if "description" in col_info:
                    self.collectionInfo.setText(str(col_info['id']) + ': ' + str(col_info['description']))

    def backend_info(self):
        """
        Loads the backend info into the backend info text field.
        """
        backend_info = self.backend.get_metadata()

        if "description" in backend_info:
            self.backendInfo.setText(str(backend_info["description"]))

    def pr_info(self):
        """
        Loads the process info into the process info dialog and shows it.
        """
        process = self.backend.get_process(str(self.processBox.currentText()))

        if not process:
            return

        self.infoWindow2 = QDialog(parent=self)
        hbox2 = QHBoxLayout()
        info_box = QTextEdit()

        if process.returns:
            info_box.setText(
                str(str(process.id) + ': ' + str(process.description) + "\n\n Returns: \n" +
                    str(process.get_return_type()) + "\n" + process.returns["description"]))
        else:
            info_box.setText(
                str(str(process.id) + ': ' + str(process.description)))

        info_box.setReadOnly(True)
        info_box.setMinimumWidth(500)
        info_box.setMinimumHeight(500)
        hbox2.addWidget(info_box)
        self.infoWindow2.setLayout(hbox2)
        self.infoWindow2.setWindowTitle('Process Information')
        self.infoWindow2.show()

    def job_info(self, job_id):
        """
        Returns detailed information about a submitted batch job in a PopUp-Window, such as:
        - Start time
        - Description
        - Progress
        - Cost
        - ...
        :param row: Integer number of the row the button is clicked.
        """

        job = self.backend.detailed_job(job_id)

        self.dlg = JobDetailDialog(iface=self.iface, job=job, backend=self.backend)
        self.dlg.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.dlg.show()

    def service_info(self, row):
        """
        Returns detailed information about a submitted service in a PopUp-Window, such as:
        - Start time
        - Description
        - Progress
        - Cost
        - ...
        :param row: Integer number of the row the button is clicked.
        """
        service = self.services_table[row]
        service_info = self.backend.service_info(service.id)
        self.infoWindow5 = QDialog(parent=self)
        hbox = QHBoxLayout()
        info_box = QTextEdit()
        info_box.setText(str(service_info))
        info_box.setReadOnly(True)
        hbox.addWidget(info_box)
        self.infoWindow5.setLayout(hbox)
        self.infoWindow5.setWindowTitle('Service Information')
        self.infoWindow5.show()

    def init_jobs(self):
        """
        Initializes the jobs table
        """
        self.jobsTableWidget.clear()

        self.jobsTableWidget.setColumnCount(8)
        self.jobsTableWidget.setHorizontalHeaderLabels(['Job Title', 'Created', 'Status', 'Execute', 'Display', 'Adapt',
                                                        'Information', 'Delete'])
        header = self.jobsTableWidget.horizontalHeader()
        self.jobsTableWidget.setSortingEnabled(True)
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(7, QtWidgets.QHeaderView.ResizeToContents)

    def init_services(self):
        """
        Initializes the services table
        """
        self.servicesTableWidget.clear()

        self.servicesTableWidget.setColumnCount(6)
        self.servicesTableWidget.setHorizontalHeaderLabels(['Title', 'Description',
                                                            'Created', 'Display', 'Information', 'Delete'])

        header = self.servicesTableWidget.horizontalHeader()
        self.servicesTableWidget.setSortingEnabled(True)
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.Interactive)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QtWidgets.QHeaderView.Interactive)
        header.setSectionResizeMode(4, QtWidgets.QHeaderView.Interactive)
        header.setSectionResizeMode(5, QtWidgets.QHeaderView.Interactive)

    def jobs_changed(self, jobs):
        jobs_str = str([str(item) for item in jobs])
        # QgsMessageLog.logMessage(json.dumps(jobs_str), "something")

        new_jobs_hash = md5(jobs_str.encode()).hexdigest()

        if new_jobs_hash == self.jobs_hash:
            return False
        else:
            self.jobs_hash = new_jobs_hash
            return True

    def refresh_jobs(self):
        """
        Refreshes the job table, so fetches all jobs of the user from the backend and lists them in the table.
        This method also generates the "Execute" and "Display" buttons.
        """

        jobs = self.backend.get_jobs()

        if not isinstance(jobs, list):
            jobs = []

        if not self.jobs_changed(jobs):
            return

        self.init_jobs()
        self.jobsTableWidget.setSortingEnabled(False)
        self.jobsTableWidget.setRowCount(len(jobs))
        row = 0
        self.jobs_table = {}
        for job in jobs:

            if job.created:
                qitem = QTableWidgetItem(job.created.strftime("%Y-%m-%d_%H-%M-%S"))
                qitem.setFlags(QtCore.Qt.ItemIsEnabled)
                self.jobsTableWidget.setItem(row, 1, qitem)

            if not job.title:
                qitem = QTableWidgetItem("Untitled Job!")
                qitem.setFlags(QtCore.Qt.ItemIsEnabled)
                self.jobsTableWidget.setItem(row, 0, qitem)
            else:
                qitem = QTableWidgetItem(job.title)
                qitem.setFlags(QtCore.Qt.ItemIsEnabled)
                self.jobsTableWidget.setItem(row, 0, qitem)

            exec_btn = QPushButton(self.jobsTableWidget)
            exec_btn.setIcon(QIcon(os.path.join(os.path.dirname(__file__), 'images/execute_icon.svg')))
            exec_btn.setIconSize(QSize(21, 21))

            if job.status:
                qitem = QTableWidgetItem(job.status)
                qitem.setFlags(QtCore.Qt.ItemIsEnabled)
                self.jobsTableWidget.setItem(row, 2, qitem)

                if job.status == "finished":
                    self.jobsTableWidget.item(row, 2).setBackground(QColor(75, 254, 40, 160))
                    disp_btn = QPushButton(self.jobsTableWidget)
                    disp_btn.setIcon(QIcon(os.path.join(os.path.dirname(__file__), 'images/display_icon.svg')))
                    disp_btn.setIconSize(QSize(29, 29))
                    self.jobsTableWidget.setCellWidget(row, 4, disp_btn)
                    disp_btn.clicked.connect(lambda *args, job_id=job.id: self.job_display(job_id))
                    iface.actionZoomIn().trigger()
                elif job.status == "running":
                    self.jobsTableWidget.item(row, 2).setBackground(QColor(254, 178, 76, 200))

                elif job.status == "error":
                    self.jobsTableWidget.item(row, 2).setBackground(QColor(254, 100, 100, 200))

            self.jobsTableWidget.setCellWidget(row, 3, exec_btn)
            exec_btn.clicked.connect(lambda *args, job_id=job.id: self.job_execute(job_id))

            info_btn2 = QPushButton(self.jobsTableWidget)
            info_btn2.setIcon(QIcon(os.path.join(os.path.dirname(__file__), 'images/edit_icon.png')))
            info_btn2.setIconSize(QSize(25, 25))
            self.jobsTableWidget.setCellWidget(row, 5, info_btn2)
            info_btn2.clicked.connect(lambda *args, job_id=job.id: self.adapt_job(job_id))

            info_btn3 = QPushButton(self.jobsTableWidget)
            info_btn3.setIcon(QIcon(os.path.join(os.path.dirname(__file__), 'images/info_icon.png')))
            info_btn3.setIconSize(QSize(25, 25))
            self.jobsTableWidget.setCellWidget(row, 6, info_btn3)
            info_btn3.clicked.connect(lambda *args, job_id=job.id: self.job_info(job_id))

            info_btn4 = QPushButton(self.jobsTableWidget)
            info_btn4.setIcon(QIcon(os.path.join(os.path.dirname(__file__), 'images/deleteFinalBtn.png')))
            info_btn4.setIconSize(QSize(25, 25))
            self.jobsTableWidget.setCellWidget(row, 7, info_btn4)
            info_btn4.clicked.connect(lambda *args, job_id=job.id: self.delete_job_final(job_id))

            self.refreshButton.setEnabled(True)
            self.refreshButton_service.setEnabled(True)

            self.jobs_table[row] = job

            row += 1

        self.jobsTableWidget.setSortingEnabled(True)

    def refresh_services(self):
        """
        Refreshes the service table, so fetches all jobs of the user from the backend and lists them in the table.
        This method also generates the "Execute" and "Display" buttons.
        """

        services = self.backend.get_services()

        if not isinstance(services, list):
            services = []

        self.init_services()
        self.servicesTableWidget.setSortingEnabled(False)
        self.servicesTableWidget.setRowCount(len(services))
        row = 0
        self.services_table = {}

        for serv in services:
            if serv.title:
                if not serv.title:
                    qitem = QTableWidgetItem("Untitled Service!")
                    qitem.setFlags(QtCore.Qt.ItemIsEnabled)
                    self.servicesTableWidget.setItem(row, 0, qitem)
                else:
                    qitem = QTableWidgetItem(serv.title)
                    qitem.setFlags(QtCore.Qt.ItemIsEnabled)
                    self.servicesTableWidget.setItem(row, 0, qitem)

            if serv.description:
                qitem = QTableWidgetItem(serv.description)
                qitem.setFlags(QtCore.Qt.ItemIsEnabled)
                self.servicesTableWidget.setItem(row, 1, qitem)

            if serv.created:
                qitem = QTableWidgetItem(serv.created.strftime("%Y-%m-%d_%H-%M-%S"))
                qitem.setFlags(QtCore.Qt.ItemIsEnabled)
                self.servicesTableWidget.setItem(row, 2, qitem)

            disp_btn = QPushButton(self.servicesTableWidget)
            disp_btn.setIcon(QIcon(os.path.join(os.path.dirname(__file__), 'images/display_icon.svg')))
            disp_btn.setIconSize(QSize(29, 29))

            self.servicesTableWidget.setCellWidget(row, 3, disp_btn)
            disp_btn.clicked.connect(lambda *args, servi=serv: self.service_execute(servi.url, servi.id))

            info_btn = QPushButton(self.servicesTableWidget)
            info_btn.setIcon(QIcon(os.path.join(os.path.dirname(__file__), 'images/info_icon.png')))
            info_btn.setIconSize(QSize(25, 25))
            self.servicesTableWidget.setCellWidget(row, 4, info_btn)
            info_btn.clicked.connect(lambda *args, srow=row: self.service_info(srow))

            del_btn = QPushButton(self.servicesTableWidget)
            del_btn.setIcon(QIcon(os.path.join(os.path.dirname(__file__), 'images/deleteFinalBtn.png')))
            del_btn.setIconSize(QSize(25, 25))
            self.servicesTableWidget.setCellWidget(row, 5, del_btn)
            del_btn.clicked.connect(lambda *args, srow=row: self.delete_service_final(srow))

            self.services_table[row] = serv

            row += 1
        self.servicesTableWidget.setSortingEnabled(True)

    def service_execute(self, url, s_id):
        """
        Executes the service of the given url and Id.
        This method is called after the "Execute" button is clicked at the service table.
        :param url: str: URL where the service is provided.
        :param s_id: str: Service identifier.
        """
        url_param = 'type=xyz&url={}'.format(url)

        rlayer = QgsRasterLayer(url_param, 'OpenEO-{}'.format(s_id), 'wms')

        if rlayer.isValid():
            QgsProject.instance().addMapLayer(rlayer)
        else:
            warning(self.iface, 'invalid layer')

    def job_execute(self, job_id):
        """
        Executes the job of the given row of the job table.
        This method is called after the "Execute" button is clicked at the job table.
        :param job_id: Integer number of the job id the button is clicked.
        """
        resp = self.backend.job_start(job_id)

        #if resp.status_code:
        #error(self.iface, str(resp))
        # warning(self.iface, str(resp))
        self.refresh_jobs()

    def adapt_job(self, job_id):
        """
        Opens an adaption dialog of the job on the given row of the job table.
        This method is called after the "Adapt" button is clicked at the job table.
        :param job_id: Integer number of the job id the button is clicked.
        """

        job = self.backend.detailed_job(job_id)

        self.dlg = JobAdaptDialog(iface=self.iface, job=job, backend=self.backend, main_dia=self)
        self.dlg.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.dlg.show()

    def job_display(self, job_id):
        """
        Displays the job of the given row of the job table on a new QGis Layer.
        This method is called after the "Display" button is clicked at the job table.
        :param job_id: Integer number of the job id the button is clicked.
        """
        job = self.backend.get_job(job_id)
        process_graph_job = self.backend.job_pg_info(job_id)
        download_dir = self.backend.job_result_download(job_id)
        if download_dir:
            for ddir in download_dir:
                info(self.iface, "Downloaded to {}".format(ddir))
                result = Result(path=ddir, process_graph=process_graph_job)
                if iface.activeLayer():
                    crs_background = iface.activeLayer().crs().authid()
                    QSettings().setValue('/Projections/defaultBehaviour', 'useGlobal')
                    QSettings().setValue('/Projections/layerDefaultCrs', crs_background)
                else:
                    QSettings().setValue('/Projections/defaultBehaviour', 'useGlobal')
                    QSettings().setValue('/Projections/layerDefaultCrs', 'EPSG:4326')

                if job.title:
                    title = job.title
                else:
                    title = "NoTitle"

                result.display(layer_name="{}-{}".format(title, job.created.strftime("%Y-%m-%d_%H-%M-%S")))
                iface.zoomToActiveLayer()

        self.refresh_jobs()

    def delete_job_final(self, job_id):
        """
        Opens an deletion dialog of the job on the given row of the job table.
        This method is called after the "Delete" button is clicked at the job table.
        :param row: Integer number of the row the button is clicked.
        """
        job = self.backend.get_job(job_id)
        sure = self.yes_no_dialog("Are you sure you want to delete Job '{}'?".format(job.title))

        if not sure:
            return

        self.backend.job_delete(job_id)
        self.refresh_jobs()

    def yes_no_dialog(self, message):
        """
        Opens a yes/no dialog with the given message.
        :param message: str: Message that should be shown on the dialog.
        :returns answer: bool: True if "Yes" was chosen, else False.
        """
        reply = QMessageBox.question(self, "Are you sure?",
                                     message, QMessageBox.Yes, QMessageBox.Cancel)

        if reply == QMessageBox.Yes:
            return True
        else:
            return False

    def delete_service_final(self, row):
        """
        Opens an deletion dialog of the service on the given row of the service table.
        This method is called after the "Delete" button is clicked at the service table.
        :param row: Integer number of the row the button is clicked.
        """
        service = self.services_table[row]

        sure = self.yes_no_dialog("Are you sure you want to delete Service '{}'?".format(service.title))

        if not sure:
            return

        self.backend.service_delete(service.id)
        self.refresh_services()

    def process_selected(self):
        """
        Gets called if a new process is selected at the process combobox.
        It loads all arguments with their type and an example (if exist) into the value
        """
        self.processTableWidget.clear()
        pr = self.backend.get_process(str(self.processBox.currentText()))

        if not pr:
            return

        self.returnLabel.setText(str(pr.get_return_type()))

        self.processTableWidget.setRowCount(len(pr.parameters))
        self.processTableWidget.setColumnCount(3)
        self.processTableWidget.setHorizontalHeaderLabels(['Parameter', 'Type', 'Description'])
        header = self.processTableWidget.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.Stretch)

        counter = 0
        for param in pr.parameters:
            qitem = QTableWidgetItem(param.name)
            qitem.setFlags(QtCore.Qt.ItemIsEnabled)

            if not param.optional:
                bold_font = QtGui.QFont()
                bold_font.setBold(True)
                qitem.setFont(bold_font)

            self.processTableWidget.setItem(counter, 0, qitem)

            param_type = QTableWidgetItem(str(param.get_type()))
            param_type.setFlags(QtCore.Qt.ItemIsEnabled)
            self.processTableWidget.setItem(counter, 1, param_type)

            if param.description:
                desc = QTableWidgetItem(str(param.description))
                desc.setFlags(QtCore.Qt.ItemIsEnabled)
                self.processTableWidget.setItem(counter, 2, desc)
            else:
                desc = QTableWidgetItem("")
                desc.setFlags(QtCore.Qt.ItemIsEnabled)
                self.processTableWidget.setItem(counter, 2, desc)

            counter += 1
