# -*- coding: utf-8 -*-
"""
/***************************************************************************
 JobAdaptDialog

 This class is responsible for adapting existing openEO jobs.

        author            : 2020 by Bernhard Goesswein
        email             : bernhard.goesswein@geo.tuwien.ac.at
 ***************************************************************************/
"""
import webbrowser
import os
import json
from copy import deepcopy
import ast
from qgis.PyQt import uic

from PyQt5 import QtWidgets, QtCore, QtGui

from PyQt5.QtWidgets import QApplication, QComboBox, QMessageBox, QDialog, QHBoxLayout, QTextEdit
from qgis.PyQt.QtWidgets import QTableWidgetItem, QPushButton, QApplication

from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtCore import Qt, QSize, QDate
from .utils.logging import warning, error

from .spatial_dialog import SpatialDialog
from .temp_dialog import TempDialog
from .band_dialog import BandDialog
########################################################################################################################
########################################################################################################################

# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'job_adapt_dialog.ui'))


class JobAdaptDialog(QtWidgets.QDialog, FORM_CLASS):
    """
    This class is responsible for adapting existing openEO jobs.
    """
    def __init__(self, parent=None, iface=None, job=None, backend=None, subgraph=None, row=0, main_dia=None):
        """
        Constructor method: Initializing the button behaviours and the Table entries.
        :param parent: parent dialog of this dialog (e.g. OpenEODialog).
        :param iface: Interface to show the dialog.
        :param job: models.Job: Job that should be adapted
        :param backend: Backend: Currently connected backend.
        :param subgraph: dict: Usually None, but if the JobAdaptDialog is called for a subgraph
                               (e.g. when using a reducer), it contains the process graph to be edited.
        :param row: Int: row of the process graph table widget related to the process to edit.
        :param main_dia: JobAdaptDialog: Contains the parent JobAdaptDialog object, if a subgraph is given.
        """
        super(JobAdaptDialog, self).__init__(parent)

        QApplication.setStyle("cleanlooks")
        self.setupUi(self)

        self.iface = iface
        self.job = job
        self.backend = backend
        self.main_dia = main_dia

        self.cur_process = None
        self.cur_node = None
        self.cur_row = None
        self.dlg = None
        self.temp_dialog = None
        self.spatial_dialog = None
        self.band_dialog = None

        self.processgraph_buffer = None

        # Raw graph
        self.rawgraphBtn.clicked.connect(self.raw_graph)

        self.manualButton.clicked.connect(self.user_manual)

        # Init Process graph
        if self.job.process.process_graph:
            self.processgraph_buffer = deepcopy(self.job.process.process_graph)

        # IF subgraph
        self.subgraph = subgraph
        self.row = row

        if subgraph:
            self.setWindowTitle("Adapt Parameter")
            self.adaptButton.hide()
            self.sendButton.setText("Adapt")
            self.sendButton.clicked.connect(self.send_pg)
            self.processgraph_buffer = json.loads(subgraph)["process_graph"]
            self.titleText.hide()
            self.label_8.hide()
            self.label_10.hide()
            self.descriptionText.hide()
            self.manualButton.hide()
            self.jobGroupBox.setTitle("Subgraph Editor")
            self.manageGroupBox.setTitle("Manage Subgraph")
        else:
            if job.description:
                self.descriptionText.setText(job.description)
            if job.title:
                self.titleText.setText(job.title)
            self.sendButton.clicked.connect(self.send_job)
            if job.id:
                self.adaptButton.clicked.connect(self.adapt_job)
            else:
                self.adaptButton.hide()

        self.process_graph_to_table()

        self.cancelButton.clicked.connect(self.close)
        self.reset_processBtn.clicked.connect(self.reset_process)

        self.resultCheckBox.stateChanged.connect(self.update_result_node)

        self.newprocessButton.clicked.connect(self.add_new_process)
        self.saveprocessButton.clicked.connect(self.set_process_by_cur_node)
        self.cloneprocessButton.clicked.connect(self.clone_process)

        self.processesComboBox.addItem("Select a process")
        for key, val in self.backend.get_processes().items():
            self.processesComboBox.addItem(key)

        self.processesComboBox.currentTextChanged.connect(self.process_selected)
        self.processIdText.setText("")

        self.rawgraph_window = None
        self.raw_pg_box = None

    def hide(self):
        super(JobAdaptDialog, self).hide()

        if self.main_dia:
            self.main_dia.hide()

    def show(self):
        if self.main_dia:
            self.main_dia.show()
        super(JobAdaptDialog, self).show()

    def user_manual(self):
        """
        Shows the user manual window.
        """
        try:
            webbrowser.open("https://openeo.org/documentation/1.0/qgis/#adapting-existing-jobs")
        except:
            pass

    def process_selected(self):
        """
        Gets called if a process in the "add process" combobox is selected.
        Generates a process identifier and loads the parameters to the process table widget.
        """
        if self.processesComboBox.currentText() == "Select a process":
            return

        counter = 1
        p_id = "{}{}".format(self.processesComboBox.currentText().lower(), str(counter))
        while p_id in self.processgraph_buffer:
            counter += 1
            p_id = "{}{}".format(self.processesComboBox.currentText().lower(), str(counter))
        self.processIdText.setText(p_id)
        self.new_process_to_table(self.processesComboBox.currentText())

    def raw_graph(self):
        """
        Shows the raw process graph window, to copy paste graphs.
        """
        self.rawgraph_window = QDialog(parent=self)
        hbox = QHBoxLayout()
        self.raw_pg_box = QTextEdit()
        self.raw_pg_box.setText(json.dumps({"process_graph": self.processgraph_buffer}, indent=4))
        self.raw_pg_box.setReadOnly(False)
        hbox.addWidget(self.raw_pg_box)
        apply_btn = QPushButton('Apply')
        hbox.addWidget(apply_btn)
        close_btn = QPushButton('Close')
        hbox.addWidget(close_btn)
        apply_btn.clicked.connect(self.receive_process_graph)
        close_btn.clicked.connect(self.rawgraph_window.close)

        self.rawgraph_window.setMinimumHeight(600)
        self.rawgraph_window.setMinimumWidth(400)
        self.rawgraph_window.setLayout(hbox)
        self.rawgraph_window.setWindowTitle('Service Information')
        self.rawgraph_window.show()

    def is_cur_node_new_process(self):
        return self.cur_node not in self.processgraph_buffer

    def enable_save_changes_button(self):
        if not self.is_cur_node_new_process():
            self.saveprocessButton.setEnabled(True)

    def receive_process_graph(self):
        """
        Apply changes of the raw process graph window to the current adapted job.
        """
        try:
            self.processgraph_buffer = json.loads(self.raw_pg_box.toPlainText()).get("process_graph")
            self.process_graph_to_table()
            self.rawgraph_window.close()
        except:
            warning(self.iface, "Can not load process graph! Not correct JSON!")

    def add_new_process(self):
        """
        Add the new process to the current process graph, selected and edited by the new process combobox.
        """
        node_id = self.processIdText.text()
        if not node_id:
            return

        process_id = self.processesComboBox.currentText()
        arguments = {}

        # pr_meta = self.backend.get_process(process_id)

        for pr_row in range(self.processTableWidget.rowCount()):

            if self.processTableWidget.item(pr_row, 0):
                arg_name = self.processTableWidget.item(pr_row, 0).text()

            if self.processTableWidget.item(pr_row, 2):
                value = self.processTableWidget.item(pr_row, 2).text()

            if arg_name and value:
                try:
                    arguments[arg_name] = json.loads(value)
                except:
                    arguments[arg_name] = value

            # try:
            #     if self.processTableWidget.item(pr_row, 2).text():
            #         arguments[self.processTableWidget.item(pr_row, 0).text()] = \
            #                                             json.loads(self.processTableWidget.item(pr_row, 2).text())
            # except json.decoder.JSONDecodeError:
            #     if "string" in self.processTableWidget.item(pr_row, 2).text().strip():
            #         arguments[self.processTableWidget.item(pr_row, 0).text()] = \
            #             str(self.processTableWidget.item(pr_row, 2).text())
            #     elif pr_meta.is_arg_mandatory(self.processTableWidget.item(pr_row, 0).text()):
            #         warning(self.iface, "Could not store mandatory argument {} of process {} "
            #                 .format(self.processTableWidget.item(pr_row, 0).text(), node_id))
                # arguments[self.processTableWidget.item(pr_row, 0).text()] = None

        self.processgraph_buffer[node_id] = {"arguments": arguments, "process_id": process_id}

        if self.resultCheckBox.isChecked():
            self.processgraph_buffer[node_id]["result"] = True
            self.resultCheckBox.setChecked(False)

        self.process_graph_to_table()
        self.clear_process_add_fields()
        # self.processTableWidget.clear()
        self.processTableWidget.setRowCount(0)
        self.processLabel.setText("")

    def reset_process(self):
        """
        Resets the process graph to the originally loaded one, so dropping all changes made by the user.
        """
        if not self.cur_node:
            return

        if self.subgraph:
            self.processgraph_buffer[self.cur_node] = json.loads(self.subgraph)["process_graph"][self.cur_node]
        else:
            self.processgraph_buffer[self.cur_node] = self.job.process.process_graph[self.cur_node]

        self.process_graph_to_table()
        self.process_to_table(self.cur_node, self.cur_row)

    def adapt_job(self):
        """
        Adapts the currently selected job at the backend.
        """
        if self.job:
            job_status = self.backend.job_adapt(self.job.id, self.processgraph_buffer, title=self.titleText.text(),
                                             desc=self.descriptionText.text())
            if job_status:
                error(self.iface, "Job creation failed: {}".format(str(self.backend.error_msg_from_resp(job_status))))
            else:

                self.close()

    def send_job(self):
        """
        Sends the currently defined process graph as a new job to the backend.
        """
        job_status = self.backend.job_create(self.processgraph_buffer, title=self.titleText.text(),
                                             desc=self.descriptionText.text())
        if job_status:
            error(self.iface, "Job creation failed: {}".format(str(self.backend.error_msg_from_resp(job_status))))
        else:
            self.close()

    def send_pg(self):
        """
        Sends the currently defined (sub) process graph back to the parent JobAdaptDialog.
        """
        if isinstance(self.main_dia, JobAdaptDialog):
            self.main_dia.receive_pg(self.processgraph_buffer, row=self.row)
        self.close()

    def receive_pg(self, process_graph, row):
        """
        Receives the defined (sub) process graph from the child JobAdaptDialog.
        :param process_graph: Dict: sub process graph to be set.
        :param row: Int: Row of the currently selected process argument.
        """

        self.processTableWidget.item(row, 2).setText(json.dumps({"process_graph": process_graph}))

        arg_name = self.processTableWidget.item(row, 0).text()
        value = self.processTableWidget.item(row, 2).text()

        if arg_name and value:
            if self.cur_node:
                if self.cur_node in self.processgraph_buffer:
                    self.processgraph_buffer[self.cur_node]["arguments"][arg_name] = json.loads(value)

    def init_process_table(self):
        """
        Initializes the process table by setting the column settings and headers.
        """
        self.processTableWidget.clear()
        self.processTableWidget.setColumnCount(4)
        self.processTableWidget.setHorizontalHeaderLabels(['Argument', 'Type', 'Value', 'Edit'])
        header = self.processTableWidget.horizontalHeader()
        self.processTableWidget.setSortingEnabled(True)
        self.processTableWidget.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.Interactive)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.Interactive)
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.Stretch)
        header.setSectionResizeMode(3, QtWidgets.QHeaderView.Interactive)

    def incompatible_process_to_table(self, p_id, row):
        """
        Loads the arguments of a process to to the process table, which the backend does not provides.
        :param p_id: str: Process identifier of the incompatible process
        :param row: int: Row number of the process on the process graph table.
        """
        self.cur_process = self.get_process_by_node_id(p_id)

        if not self.cur_process:
            return

        self.mark_pg_row(row)

        self.init_process_table()

        arguments = self.cur_process["arguments"]

        self.processTableWidget.setRowCount(len(arguments))

        par_row = 0
        for key, val in arguments.items():
            qitem = QTableWidgetItem(key)
            qitem.setFlags(QtCore.Qt.ItemIsEnabled)

            self.processTableWidget.setItem(par_row, 0, qitem)

            p_type = QTableWidgetItem("Unknown to backend")
            p_type.setFlags(QtCore.Qt.ItemIsEnabled)
            self.processTableWidget.setItem(par_row, 1, p_type)

            if val:
                val_item = QTableWidgetItem(json.dumps(val))
            else:
                val_item = QTableWidgetItem("")

            self.processTableWidget.setItem(par_row, 2, val_item)
            par_row += 1
        self.cloneprocessButton.setEnabled(True)
        self.saveprocessButton.setEnabled(False)

    def mark_pg_row(self, row):
        """
        Marks a row / process on the process graph table visually.
        :param row: int: Row number of the process on the process graph table.
        """
        for pr_row in range(self.processgraphTableWidget.rowCount()):
            for pr_col in range(self.processgraphTableWidget.columnCount()):
                if self.processgraphTableWidget.item(pr_row, pr_col):
                    if pr_row == row:
                        self.processgraphTableWidget.item(pr_row, pr_col).setBackground(Qt.lightGray)
                    else:
                        self.processgraphTableWidget.item(pr_row, pr_col).setBackground(Qt.white)

    def set_complex_edit_element(self, param, p_id, value, row):
        """
        Adds a complex edit element to the process table (e.g. drop down to select predecessor process).
        :param param: Parameter: parameter the complex edit should be applied.
        :param p_id: str: Process identifier (e.g. load_collection).
        :param value: str/dict: Current value of the argument in the process graph.
        :param row: int: Row number of the argument on the process table.
        """
        # Special processes to handle
        if ((p_id == "load_collection") and (str(param.name) == "id")) or ("collection-id" in str(param.get_type())):
            id_combo = QComboBox()
            all_collections = self.backend.get_collections()
            for col in all_collections:
                if "id" in col:
                    id_combo.addItem(col['id'])
            if value:
                id_combo.setCurrentText(str(value))
            self.processTableWidget.setCellWidget(row, 3, id_combo)
            id_combo.currentTextChanged.connect(lambda *args, srow=row,
                                                       scombo=id_combo: self.update_combobox_selection(scombo, srow))

        # Edit stuff for special values regarding parameter names
        if str(param.name) == "dimension":
            dim_combo = QComboBox()
            all_dimensions = self.backend.get_dimensions(self.get_collection_id())
            for dim in all_dimensions:
                dim_combo.addItem(dim)
            if value in [dim_combo.itemText(i) for i in range(dim_combo.count())]:
                dim_combo.setCurrentText(str(value))
            self.processTableWidget.setCellWidget(row, 3, dim_combo)
            dim_combo.currentTextChanged.connect(lambda *args, srow=row,
                                                       scombo=dim_combo: self.update_combobox_selection(scombo, srow))

        # Edit stuff for special values regarding types
        if ("geojson" in str(param.get_type())) or ("bounding-box" in str(param.get_type())):
            edit_btn = QPushButton(self.processgraphTableWidget)
            edit_btn.setIcon(QIcon(os.path.join(os.path.dirname(__file__), 'images/edit_icon.png')))
            edit_btn.setIconSize(QSize(25, 25))
            self.processTableWidget.setCellWidget(row, 3, edit_btn)
            edit_btn.clicked.connect(lambda *args, rrow=row: self.adapt_spatial(rrow))
            return edit_btn
        elif "raster-cube" in str(param.get_type()):
            id_combo = QComboBox()
            id_combo.addItem("Select")
            id_combo.addItems(self.get_process_id_list(exception=p_id))
            if value:
                if "from_node" in value:
                    id_combo.setCurrentText(str(value["from_node"]))
            self.processTableWidget.setCellWidget(row, 3, id_combo)
            id_combo.currentTextChanged.connect(lambda *args, irow=row,
                                                combo=id_combo: self.update_cube_selection(combo, irow))
        elif "temporal-interval" in str(param.get_type()):
            edit_btn = QPushButton(self.processgraphTableWidget)
            edit_btn.setIcon(QIcon(os.path.join(os.path.dirname(__file__), 'images/edit_icon.png')))
            edit_btn.setIconSize(QSize(25, 25))
            self.processTableWidget.setCellWidget(row, 3, edit_btn)
            edit_btn.clicked.connect(lambda *args, irow=row: self.adapt_temporal(irow))
        elif "process-graph" in str(param.get_type()):
            edit_btn = QPushButton(self.processgraphTableWidget)
            edit_btn.setIcon(QIcon(os.path.join(os.path.dirname(__file__), 'images/edit_icon.png')))
            edit_btn.setIconSize(QSize(25, 25))
            self.processTableWidget.setCellWidget(row, 3, edit_btn)
            edit_btn.clicked.connect(lambda *args, irow=row: self.adapt_pg(irow))
        elif str(param.get_type()) == "output-format":
            format_combo = QComboBox()
            all_formats = self.backend.get_output_formats()
            for formt in all_formats:
                format_combo.addItem(formt)
            if value in [format_combo.itemText(i) for i in range(format_combo.count())]:
                format_combo.setCurrentText(str(value))
            self.processTableWidget.setCellWidget(row, 3, format_combo)
            format_combo.currentTextChanged.connect(lambda *args, srow=row,
                                                        scombo=format_combo: self.update_combobox_selection(scombo, srow))

        # Special parameter names
        if "bands" in str(param.name):
            edit_btn = QPushButton(self.processgraphTableWidget)
            edit_btn.setIcon(QIcon(os.path.join(os.path.dirname(__file__), 'images/edit_icon.png')))
            edit_btn.setIconSize(QSize(25, 25))
            self.processTableWidget.setCellWidget(row, 3, edit_btn)
            edit_btn.clicked.connect(lambda *args, irow=row: self.adapt_bands(irow))

        if self.subgraph:
            if not self.processTableWidget.item(row, 3):
                edit_btn = QPushButton(self.processgraphTableWidget)
                edit_btn.setText("Proc-Param")
                self.processTableWidget.setCellWidget(row, 3, edit_btn)
                edit_btn.clicked.connect(lambda *args, irow=row: self.set_process_param(irow))

    def new_process_to_table(self, process_id):
        """
        Gets called if a new process is selected at the "add process" combo box.
        It loads all arguments with their types into the process table.
        """
        self.processTableWidget.clear()
        self.cur_process = None
        self.cur_node = None
        self.cur_row = None

        # Set label with the process name and the bold font

        pr = self.backend.get_process(process_id)

        p_id = self.processIdText.text()

        self.processLabel.setText("New Process: {}".format(p_id))
        my_font = QtGui.QFont()
        my_font.setBold(True)
        self.processLabel.setFont(my_font)

        self.init_process_table()
        self.processTableWidget.setRowCount(len(pr.parameters))

        par_row = 0
        for param in pr.parameters:
            qitem = QTableWidgetItem(param.name)
            qitem.setFlags(QtCore.Qt.ItemIsEnabled)

            if not param.optional:
                bold_font = QFont()
                bold_font.setBold(True)
                qitem.setFont(bold_font)

            self.processTableWidget.setItem(par_row, 0, qitem)

            p_type = QTableWidgetItem(str(param.get_type()))
            p_type.setFlags(QtCore.Qt.ItemIsEnabled)
            self.processTableWidget.setItem(par_row, 1, p_type)

            val_item = QTableWidgetItem("")

            if "process-graph" in str(param.get_type()):
                val_item = QTableWidgetItem('{ "process_graph": {} }')

            self.processTableWidget.setItem(par_row, 2, val_item)
            self.set_complex_edit_element(param, process_id, "", par_row)

            par_row += 1

        self.resultCheckBox.setChecked(False)
        self.processTableWidget.resizeRowsToContents()
        self.cloneprocessButton.setEnabled(False)

    def clear_process_add_fields(self):
        self.processesComboBox.setCurrentText("Select a process")
        self.processIdText.setText("")

    def clear_process_table(self):
        self.clear_process_add_fields()
        self.processTableWidget.clear()
        self.init_process_table()
        self.processTableWidget.setRowCount(0)

    def process_to_table(self, node_id, row):
        """
        Loads a process from the process graph table to the process table.
        :param node_id: str: Identifier of the node
        :param row: int: Row of the process graph table of the process to load.
        """
        self.clear_process_add_fields()
        self.processTableWidget.clear()
        self.cur_process = self.get_process_by_node_id(node_id)
        self.cur_node = node_id
        self.cur_row = row

        if not self.cur_process:
            return

        # Set label with the process name and the bold font

        pr = self.backend.get_process(self.cur_process["process_id"])

        my_font = QtGui.QFont()
        my_font.setBold(True)

        if not pr:
            self.processLabel.setText("Process: {} (not compatible with the backend)".format(node_id))
            self.processLabel.setFont(my_font)
            warning(self.iface, "Process '{}' not available at this backend"
                    .format(str(self.cur_process["process_id"])))
            self.incompatible_process_to_table(node_id, row)
            return

        self.processLabel.setText("Process: {}".format(node_id))
        self.processLabel.setFont(my_font)

        self.mark_pg_row(row)

        self.init_process_table()
        self.processTableWidget.setRowCount(len(pr.parameters))

        par_row = 0
        for param in pr.parameters:
            qitem = QTableWidgetItem(param.name)
            qitem.setFlags(QtCore.Qt.ItemIsEnabled)

            if not param.optional:
                bold_font = QFont()
                bold_font.setBold(True)
                qitem.setFont(bold_font)

            self.processTableWidget.setItem(par_row, 0, qitem)

            p_type = QTableWidgetItem(str(param.get_type()))
            p_type.setFlags(QtCore.Qt.ItemIsEnabled)
            self.processTableWidget.setItem(par_row, 1, p_type)

            if "arguments" in self.cur_process:
                value = self.cur_process["arguments"]
                if param.name in value:
                    value = value[param.name]
                else:
                    value = ""
            if value:
                val_item = QTableWidgetItem(json.dumps(value))
            elif isinstance(value, int):
                val_item = QTableWidgetItem(json.dumps(0))
            else:
                val_item = QTableWidgetItem("")

            self.processTableWidget.setItem(par_row, 2, val_item)
            self.set_complex_edit_element(param, node_id, value, par_row)

            par_row += 1

        if "result" in self.cur_process:
            if self.cur_process["result"]:
                self.resultCheckBox.setChecked(True)
            else:
                self.resultCheckBox.setChecked(False)
        else:
            self.resultCheckBox.setChecked(False)

        self.processTableWidget.cellChanged.connect(self.enable_save_changes_button)
        self.processTableWidget.resizeRowsToContents()
        self.cloneprocessButton.setEnabled(True)
        self.saveprocessButton.setEnabled(False)

    def update_result_node(self):
        """
        Updates the result node on the current process regarding to the result checkbox.
        """
        if not self.cur_node:
            return

        self.saveprocessButton.setEnabled(True)

        if self.resultCheckBox.isChecked():
            self.processgraph_buffer[self.cur_node]["result"] = True
        else:
            if "result" in self.processgraph_buffer[self.cur_node]:
                self.processgraph_buffer[self.cur_node].pop("result")

    def update_cube_selection(self, combo, row):
        """
        Updates the predecessor setting in the process definition regarding to the combo box.
        :param: combo: ComboBoxWidget: The combobox with the predecessor name.
        :param: row: int: Row of the argument in the process table.
        """
        selection = combo.currentText()

        if selection == "Select":
            return

        self.processTableWidget.item(row, 2).setText(json.dumps({'from_node': str(selection)}))

    def update_combobox_selection(self, combo, row):
        """
        Updates the collection setting in the process definition regarding to the combo box.
        :param: combo: ComboBoxWidget: The combobox with the collection id.
        :param: row: int: Row of the argument in the process table.
        """

        selection = combo.currentText()

        self.processTableWidget.item(row, 2).setText(selection)

    def get_process_id_list(self, exception=None):
        """
        Returns all available process identifiers of the process graph except the given exception.
        :param exception: str: Process identifier that should be excluded in the list.
        :returns id_list: list: List of process identifiers (strings)
        """
        id_list = []
        row_count = self.processgraphTableWidget.rowCount()
        for row in range(row_count):
            id_text = self.processgraphTableWidget.item(row, 0).text()
            if id_text != exception:
                id_list.append(id_text)
        return id_list

    def init_process_graph_table(self):
        """
        Initializes the process graph table by setting the column settings and headers.
        """
        self.processgraphTableWidget.clear()
        self.processgraphTableWidget.setColumnCount(5)
        self.processgraphTableWidget.setHorizontalHeaderLabels(['Id', 'Process', 'Predecessor', 'Edit', 'Del'])
        header = self.processgraphTableWidget.horizontalHeader()
        self.processgraphTableWidget.setSortingEnabled(True)
        self.processgraphTableWidget.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.Interactive)
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.Interactive)
        header.setSectionResizeMode(3, QtWidgets.QHeaderView.Stretch)
        header.setSectionResizeMode(4, QtWidgets.QHeaderView.Interactive)
        self.processgraphTableWidget.setSelectionBehavior(QtWidgets.QTableView.SelectRows)

    def set_process_graph_widget(self, node_id, process, row):
        """
        Sets a row in the process graph table according to the given process and node id.
        :param node_id: str: Identifier of the node in the process graph.
        :param process: Process: Process object that should be displayed.
        :param row: int: Row number of the process graph table.
        """
        # Id
        qitem1 = QTableWidgetItem(str(node_id))
        qitem1.setFlags(QtCore.Qt.ItemIsEnabled)
        self.processgraphTableWidget.setItem(row, 0, qitem1)

        # Process
        qitem2 = QTableWidgetItem(process["process_id"])
        qitem2.setFlags(QtCore.Qt.ItemIsEnabled)
        self.processgraphTableWidget.setItem(row, 1, qitem2)

        # Predecessor
        qitem3 = QTableWidgetItem("")
        if "data" in process["arguments"]:
            if not process["arguments"]["data"]:
                qitem3 = QTableWidgetItem("")
            elif "from_node" in process["arguments"]["data"]:
                qitem3 = QTableWidgetItem(process["arguments"]["data"]["from_node"])
        qitem3.setFlags(QtCore.Qt.ItemIsEnabled)
        self.processgraphTableWidget.setItem(row, 2, qitem3)

        # Edit
        edit_btn = QPushButton(self.processgraphTableWidget)
        edit_btn.setIcon(QIcon(os.path.join(os.path.dirname(__file__), 'images/edit_icon.png')))
        edit_btn.setIconSize(QSize(25, 25))
        self.processgraphTableWidget.setCellWidget(row, 3, edit_btn)
        edit_btn.clicked.connect(lambda *args, n_id=node_id, p_row=row: self.process_to_table(n_id, p_row))

        # Delete
        edit_btn = QPushButton(self.processgraphTableWidget)
        edit_btn.setIcon(QIcon(os.path.join(os.path.dirname(__file__), 'images/deleteFinalBtn.png')))
        edit_btn.setIconSize(QSize(25, 25))
        self.processgraphTableWidget.setCellWidget(row, 4, edit_btn)
        edit_btn.clicked.connect(lambda *args, n_id=node_id: self.delete_node(n_id))

    def delete_node(self, node_id):
        """
        Deletes a node from the process graph
        :param node_id: str: Identifier of the node to be deleted.
        """
        reply = QMessageBox.question(self, "Are you sure?",
                                     "Do you really want to remove node {}".format(str(node_id)),
                                     QMessageBox.Yes, QMessageBox.Cancel)

        if reply == QMessageBox.Yes:
            if node_id in self.processgraph_buffer:
                self.processgraph_buffer.pop(node_id)
                self.process_graph_to_table()

            self.clear_process_table()

    def process_graph_to_table(self):
        """
        Loads the current process graph to the process graph table.
        """
        self.init_process_graph_table()
        self.processgraphTableWidget.setRowCount(len(self.processgraph_buffer))

        row = 0
        for n_id, proc in self.processgraph_buffer.items():
            self.set_process_graph_widget(n_id, proc, row)
            row += 1

        self.processgraphTableWidget.resizeColumnsToContents()

    def get_process_by_node_id(self, node_id):
        """
        Returns the process by a given node_id
        :param node_id: str: Identifier of the node in the process graph.
        :returns process: dict: Process of the process graph, or None if the node id does not exist.
        """
        if node_id not in self.processgraph_buffer:
            return None

        return self.processgraph_buffer[node_id]

    def set_process_param(self, row):
        cur_text = self.processTableWidget.item(row, 2).text()
        var_name = self.processTableWidget.item(row, 0).text()
        param_text = json.dumps({"from_parameter": var_name})
        if cur_text != param_text:
            self.processTableWidget.item(row, 2).setText(param_text)
        else:
            self.processTableWidget.item(row, 2).setText("")

    def clone_process(self):

        if not self.cur_process:
            return

        cur_values = self.get_cur_process_table_json()

        self.processesComboBox.setCurrentText(cur_values["process_id"])
        self.process_selected()
        row_count = self.processTableWidget.rowCount()

        for row in range(row_count):
            arg_name = self.processTableWidget.item(row, 0).text()
            # warning(self.iface, "cur_values: {}".format(str(cur_values)))
            if arg_name.strip() in cur_values.get("arguments"):
                self.processTableWidget.item(row, 2).setText(json.dumps(cur_values.get("arguments")[arg_name]))

        self.cloneprocessButton.setEnabled(False)
        self.saveprocessButton.setEnabled(False)

    def set_process_by_cur_node(self):
        """
        Stores the current process of the process table into the process graph.
        """
        self.set_process_by_node_id(self.cur_node)
        self.saveprocessButton.setEnabled(False)

    def get_cur_process_table_json(self):
        node_id = self.cur_node
        process = self.get_process_by_node_id(node_id)

        row_count = self.processTableWidget.rowCount()

        for row in range(row_count):
            if process:
                arg_name = None
                value = None
                if self.processTableWidget.item(row, 0):
                    arg_name = self.processTableWidget.item(row, 0).text()

                if self.processTableWidget.item(row, 2):
                    value = self.processTableWidget.item(row, 2).text()

                if arg_name and value:
                    try:
                        process["arguments"][arg_name] = json.loads(value)
                    except:
                        process["arguments"][arg_name] = value
        return process

    def set_process_by_node_id(self, node_id):
        """
        Stores the process identified by the node_id of the process table into the process graph.
        :param node_id: str: Identifier of the node to be stored in the process graph.
        """
        process = self.get_process_by_node_id(node_id)

        row_count = self.processTableWidget.rowCount()

        for row in range(row_count):
            if process:
                arg_name = None
                value = None
                if self.processTableWidget.item(row, 0):
                    arg_name = self.processTableWidget.item(row, 0).text()

                if self.processTableWidget.item(row, 2):
                    value = self.processTableWidget.item(row, 2).text()

                if arg_name and value:
                    try:
                        self.processgraph_buffer[node_id]["arguments"][arg_name] = json.loads(value)
                    except:
                        self.processgraph_buffer[node_id]["arguments"][arg_name] = value

    def get_collection_id(self):
        """
        Returns the collection id of the first load_collection process found in the process graph.
        :returns col_id: str: Identifier of the current collection.
        """
        process_graph = self.processgraph_buffer

        if not process_graph:
            return None

        col_id = None

        for p_id, proc in process_graph.items():
            if proc["process_id"] == "load_collection":
                col_id = proc["arguments"].get("id")

        if not col_id:
            row_count = self.processTableWidget.rowCount()

            for row in range(row_count):
                if self.processTableWidget.item(row, 1).text().strip() == "collection-id":
                    col_id = self.processTableWidget.item(row, 2).text().strip()

        return col_id

    def adapt_pg(self, row):
        """
        Adapting a sub process graph in the process table. Starts a new dialog window.
        :param row: int: Argument row number with the process graph.
        """
        value = self.processTableWidget.item(row, 2).text()
        self.dlg = JobAdaptDialog(iface=self.iface, job=self.job, backend=self.backend,
                                  subgraph=value, row=row, main_dia=self)
        self.dlg.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.dlg.show()

    def adapt_bands(self, row):
        """
        Adapting a band selection in the process table. Starts a new dialog window.
        :param row: int: Argument row number with the bands.
        """
        sel_bands = self.processTableWidget.item(row, 2).text()
        if sel_bands:
            sel_bands = ast.literal_eval(sel_bands)
        else:
            sel_bands = []

        cur_collection = self.get_collection_id()

        if cur_collection:
            all_bands = self.backend.get_bands(cur_collection)
        else:
            all_bands = []

        self.band_dialog = BandDialog(iface=self.iface, parent=self,
                                      bands=sel_bands, all_bands=all_bands)

        self.band_dialog.show()
        self.band_dialog.raise_()
        self.band_dialog.activateWindow()

    def adapt_spatial(self, row):
        """
        Adapting the spatial extent in the process table. Starts a new dialog window.
        :param row: int: Argument row number with the spatial extent.
        """
        extent = self.processTableWidget.item(row, 2).text()

        try:
            extent = ast.literal_eval(extent)
        except:
            extent = {}

        self.spatial_dialog = SpatialDialog(interface=self.iface, parent=self, extent=extent)

        self.spatial_dialog.show()
        self.spatial_dialog.raise_()
        self.spatial_dialog.activateWindow()

    def adapt_temporal(self, row):
        """
        Adapting the temporal extent in the process table. Starts a new dialog window.
        :param row: int: Argument row number with the temporal extent.
        """
        extent = self.processTableWidget.item(row, 2).text()

        try:
            extent = ast.literal_eval(extent)
        except:
            extent = []

        col_max = None
        col_min = None

        cur_col_id = self.get_collection_id()
        if cur_col_id:
            col_extent = self.backend.get_temporal_extent_col(cur_col_id)

            for interval in col_extent:
                if interval[0]:
                    interval_sdate = QDate.fromString(interval[0][0:10], 'yyyy-MM-dd')
                    if not col_min:
                        col_min = interval_sdate
                    else:
                        if col_min > interval_sdate:
                            col_min = interval_sdate
                if interval[1]:
                    interval_edate = QDate.fromString(interval[1][0:10], 'yyyy-MM-dd')
                    if not col_max:
                        col_max = interval_edate
                    else:
                        if col_max < interval_edate:
                            col_max = interval_edate

        self.temp_dialog = TempDialog(iface=self.iface, parent=self,
                                      extent=list(extent), col_min=col_min, col_max=col_max)

        self.temp_dialog.show()
        self.temp_dialog.raise_()
        self.temp_dialog.activateWindow()

    def receive_temporal_extent(self, extent):
        """
        Receive the temporal extent from an external dialog and setting it at the value in the process table.
        :param extent: list: List of start and end date.
        """
        row_count = self.processTableWidget.rowCount()

        for row in range(row_count):
            type_text = self.processTableWidget.item(row, 1).text()
            if "temporal-interval" in type_text:
                self.processTableWidget.item(row, 2).setText(json.dumps(extent))

    def receive_spatial_extent(self, extent):
        """
        Receive the spatial extent from an external dialog and setting it at the value in the process table.
        :param extent: dict: Spatial extent dictionary
        """

        if isinstance(extent, str):
            try:
                extent = json.loads(extent)
            except json.decoder.JSONDecodeError:
                warning(self.iface, "Something went wrong during setting the extent!")
                return

        row_count = self.processTableWidget.rowCount()
        for row in range(row_count):
            type_text = self.processTableWidget.item(row, 1).text()
            if ("geojson" in type_text) or ("bounding-box" in type_text):
                self.processTableWidget.item(row, 2).setText(json.dumps(extent))

    def receive_bands(self, bands):
        """
        Receive the band selection from an external dialog and setting it at the value in the process table.
        :param bands: list: List of band identifiers
        """
        row_count = self.processTableWidget.rowCount()
        for row in range(row_count):
            arg_text = self.processTableWidget.item(row, 0).text()
            if "bands" in arg_text:
                self.processTableWidget.item(row, 2).setText(json.dumps(bands))
