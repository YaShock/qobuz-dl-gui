import os
import glob
import sys
import logging
from collections import namedtuple

from PyQt5.QtCore import Qt, QObject
from PyQt5.QtCore import pyqtSignal, pyqtSlot, QThread
from PyQt5.QtGui import QKeyEvent, QBrush
from PyQt5 import QtWidgets

from qobuz_dl_gui.qobuz_dl.core import QUALITIES

from qobuz_dl_gui import model
from qobuz_dl_gui.model import DownloadStatus
from qobuz_dl_gui.logger import QPlainTextEditLogger


class DownloadThread(QThread):
    item_started = pyqtSignal(int)
    item_finished = pyqtSignal(int)
    all_finished = pyqtSignal()

    def __init__(self, qobuz, urls):
        super().__init__()
        self.qobuz = qobuz
        self.urls = urls
        self.queue = []

    def run(self):
        if not self.urls or not isinstance(self.urls, list):
            logging.info("Nothing to download")
        else:
            self._download_urls()
        self.all_finished.emit()

    def _download_urls(self):
        for index in range(len(self.urls)):
            url_queue = []
            self.queue.append(url_queue)
            self._handle_url(self.urls[index], url_queue)

        for index in range(len(self.urls)):
            interrupt = self.isInterruptionRequested()
            if interrupt:
                break
            self.item_started.emit(index)
            url_queue = self.queue[index]
            for item in url_queue:
                interrupt = self.isInterruptionRequested()
                if interrupt:
                    break
                item()
            else:
                self.item_finished.emit(index)

    def _handle_url(self, url, queue):
        self.qobuz.handle_url(url, queue)


class MainView(QtWidgets.QWidget):
    def __init__(self, qobuz, config, config_path) -> None:
        super().__init__()
        self.qobuz = qobuz
        self.config = config
        self.config_path = config_path
        self.results = []
        # List of DownloadItems
        self.dl_queue = []
        self.dl_in_progress = False
        self.download_thread = None

        self.init_view()
        self.setMinimumSize(800, 620)
        self.setWindowTitle("Qobuz Downloader")

    def closeEvent(self, event):
        logger = logging.getLogger()
        logger.removeHandler(self.log_handler)
        self.log_handler = None
        super().closeEvent(event)

    def init_view(self):
        self.create_view_navigation_layout()

        self.create_layout_search()
        self.create_layout_download()
        self.create_layout_config()

        main_layout = QtWidgets.QHBoxLayout()
        main_layout.addWidget(self.views)
        main_layout.addWidget(self.frame_search)
        main_layout.addWidget(self.frame_download)
        main_layout.addWidget(self.frame_config)
        self.frame_download.hide()
        self.frame_config.hide()
        main_grid = QtWidgets.QFrame()
        main_grid.setLayout(main_layout)

        self.init_logging(main_grid)

    def init_logging(self, main_grid):
        vertical_grid = QtWidgets.QVBoxLayout(self)
        splitter = QtWidgets.QSplitter(Qt.Vertical)
        splitter.addWidget(main_grid)
        self.log_handler = QPlainTextEditLogger(self)
        splitter.addWidget(self.log_handler.widget)
        vertical_grid.addWidget(splitter)

        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)

        format = "%(levelname)s - %(message)s"
        self.log_handler.setFormatter(logging.Formatter(format))
        logger.addHandler(self.log_handler)

    def create_view_navigation_layout(self):
        self.views = QtWidgets.QListWidget()
        self.views.setFixedWidth(200)
        views_layout = QtWidgets.QVBoxLayout()
        views_layout.addWidget(self.views)
        item_search = QtWidgets.QListWidgetItem("Search")
        item_dl = QtWidgets.QListWidgetItem("Download Queue")
        item_cfg = QtWidgets.QListWidgetItem("Configuration")
        self.views.addItem(item_search)
        self.views.addItem(item_dl)
        self.views.addItem(item_cfg)
        self.views.setCurrentRow(0)
        self.show_view_fns = [
            self.show_search_view,
            self.show_dl_view,
            self.show_cfg_view
        ]
        self.views.itemSelectionChanged.connect(self.click_show_view)

    def click_show_view(self):
        row = self.views.currentRow()
        self.show_view_fns[row]()

    def show_search_view(self):
        self.frame_download.hide()
        self.frame_config.hide()
        self.frame_search.show()

    def show_dl_view(self):
        self.frame_search.hide()
        self.frame_config.hide()
        self.frame_download.show()

    def show_cfg_view(self):
        self.frame_search.hide()
        self.frame_download.hide()
        self.frame_config.show()

    def create_layout_search(self):
        self.line_search = QtWidgets.QLineEdit()
        self.btn_search = QtWidgets.QPushButton("Search")
        self.btn_add_dl_queue = QtWidgets.QPushButton("Add to Download")
        self.comb_search_type = QtWidgets.QComboBox()

        # Supported types for search
        self.search_types = [model.Album, model.Artist, model.Track, model.Playlist]
        for item in self.search_types:
            self.comb_search_type.addItem(item.__name__, item)
        self.comb_search_type.setCurrentText("Album")

        # init table
        column_names = ["#", "Artist", "Name", "Duration", "Quality"]
        self.table_search = self.create_search_table(column_names, 2)

        # layout
        line_grid = QtWidgets.QHBoxLayout()
        line_grid.addWidget(self.comb_search_type)
        line_grid.addWidget(self.line_search)
        line_grid.addWidget(self.btn_search)

        line_grid_2 = QtWidgets.QHBoxLayout()
        line_grid_2.addStretch(4)
        line_grid_2.addWidget(self.btn_add_dl_queue)

        search_view = QtWidgets.QVBoxLayout()
        search_view.addLayout(line_grid)
        search_view.addWidget(self.table_search)
        search_view.addLayout(line_grid_2)

        self.frame_search = QtWidgets.QFrame()
        self.frame_search.setLayout(search_view)

        # connect
        self.btn_search.clicked.connect(self.search)
        self.btn_add_dl_queue.clicked.connect(self.add_dl_queue)
        self.line_search.returnPressed.connect(self.search)

    def create_layout_download(self):
        # init table
        column_names = ["#", "Status", "Type", "Description"]
        self.table_dl = self.create_search_table(column_names, 3)

        # layout
        self.btn_clear_all = QtWidgets.QPushButton("Remove All")
        self.btn_clear_selection = QtWidgets.QPushButton("Remove Selected")
        self.btn_download = QtWidgets.QPushButton("Download")
        self.btn_stop_dl = QtWidgets.QPushButton("Stop")
        line_grid = QtWidgets.QHBoxLayout()

        line_grid_2 = QtWidgets.QHBoxLayout()
        line_grid_2.addStretch(4)
        line_grid_2.addWidget(self.btn_clear_all)
        line_grid_2.addWidget(self.btn_clear_selection)
        line_grid_2.addWidget(self.btn_download)
        line_grid_2.addWidget(self.btn_stop_dl)

        download_view = QtWidgets.QVBoxLayout()
        download_view.addLayout(line_grid)
        download_view.addWidget(self.table_dl)
        download_view.addLayout(line_grid_2)

        self.frame_download = QtWidgets.QFrame()
        self.frame_download.setLayout(download_view)

        # connect
        self.btn_clear_all.clicked.connect(self.clear_dl_queue_all)
        self.btn_clear_selection.clicked.connect(self.clear_dl_queue_selected)
        self.btn_download.clicked.connect(self.download_queue)
        self.btn_stop_dl.clicked.connect(self.stop_download)

    def create_layout_config(self):
        self.comb_quality = QtWidgets.QComboBox()
        for q, val in QUALITIES.items():
            self.comb_quality.addItem(val, q)
        self.comb_quality.setCurrentText(QUALITIES[self.qobuz.quality])

        self.sb_limit = QtWidgets.QSpinBox()
        self.sb_limit.setMinimum(10)
        self.sb_limit.setMaximum(500)
        self.sb_limit.setValue(self.qobuz.interactive_limit)

        self.line_dl_dir = QtWidgets.QLineEdit()
        self.line_dl_dir.setText(self.qobuz.directory)
        self.line_dl_dir.setDisabled(True)

        btn_dl_dir = QtWidgets.QPushButton("Downloads")
        btn_dl_dir.clicked.connect(self.get_dl_dir)
        btn_dl_dir.setStyleSheet("""
            border: none;
            padding: 0px;
        """)

        btn_save = QtWidgets.QPushButton("Save")
        btn_save.clicked.connect(self.save_config)
        btn_logout = QtWidgets.QPushButton("Log out and Quit")
        btn_logout.clicked.connect(self.logout_quit)

        # layout
        config_view = QtWidgets.QGridLayout()
        config_view.addWidget(QtWidgets.QLabel("Quality"), 0, 0)
        config_view.addWidget(self.comb_quality, 0, 1)
        config_view.addWidget(QtWidgets.QLabel("Search Limit"), 1, 0)
        config_view.addWidget(self.sb_limit, 1, 1)
        config_view.addWidget(btn_dl_dir, 2, 0)
        config_view.addWidget(self.line_dl_dir, 2, 1)
        config_view.addWidget(btn_save, 3, 0)
        config_view.addWidget(btn_logout, 3, 1)
        config_view.setRowStretch(config_view.rowCount(), 1)

        self.frame_config = QtWidgets.QFrame()
        self.frame_config.setLayout(config_view)

    def get_dl_dir(self):
        folderpath = QtWidgets.QFileDialog.getExistingDirectory(self, 'Select Folder')
        self.line_dl_dir.setText(folderpath)

    def save_config(self):
        dl_dir = self.line_dl_dir.text()
        search_limit = self.sb_limit.value()
        quality = self.comb_quality.currentData()

        self.qobuz.directory = dl_dir
        self.qobuz.interactive_limit = search_limit
        self.quality = quality

        self.config["DEFAULT"]["default_folder"] = dl_dir
        self.config["DEFAULT"]["default_limit"] = str(search_limit)
        self.config["DEFAULT"]["default_quality"] = str(quality)
        with open(self.config_path, "w") as config_file:
            self.config.write(config_file)

    def logout_quit(self):
        self.config["DEFAULT"]["email"] = ""
        self.config["DEFAULT"]["password"] = ""
        with open(self.config_path, "w") as config_file:
            self.config.write(config_file)
        self.close()

    def search(self):
        self.s_type = self.comb_search_type.currentData()
        s_type_str = self.s_type.__name__.lower()
        query = self.line_search.text()
        if len(query) == 0:
            return
        results_raw = self.qobuz.search_by_type_unformatted(
            query, s_type_str, self.qobuz.interactive_limit)
        self.results.clear()
        for result in results_raw:
            text = result["text"]
            data = result["data"]
            data = model.parse_str(s_type_str, data)
            url = result["url"]
            self.results.append((text, url, data))

        self.set_search_result(self.s_type, self.results)

    def create_search_table(self, column_names, col_stretch) -> QtWidgets.QTableWidget:
        table = QtWidgets.QTableWidget()
        table.setColumnCount(len(column_names))
        table.setRowCount(0)
        table.setShowGrid(False)
        table.verticalHeader().setVisible(False)
        table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        table.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)

        header = table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(col_stretch, QtWidgets.QHeaderView.Stretch)

        table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        table.setFocusPolicy(Qt.NoFocus)
        for index, name in enumerate(column_names):
            item = QtWidgets.QTableWidgetItem(name)
            table.setHorizontalHeaderItem(index, item)
        return table

    def add_search_item(self, row_idx: int, col_idx: int, text: str):
        if isinstance(text, str):
            item = QtWidgets.QTableWidgetItem(text)
            self.table_search.setItem(row_idx, col_idx, item)

    def add_dl_queue_item(self, row_idx: int, col_idx: int, text: str):
        if isinstance(text, str):
            item = QtWidgets.QTableWidgetItem(text)
            self.table_dl.setItem(row_idx, col_idx, item)

    def set_search_result(self, search_type: namedtuple, results: list):
        column_names = ['#'] + list(search_type._fields)

        self.table_search.clear()
        self.table_search.clearSelection()

        self.table_search.setRowCount(len(results))
        self.table_search.setColumnCount(len(column_names))

        for index, name in enumerate(column_names):
            item = QtWidgets.QTableWidgetItem(name)
            self.table_search.setHorizontalHeaderItem(index, item)

        for index, result in enumerate(results):
            self.add_search_item(index, 0, str(index + 1))
            for attr_i, attr in enumerate(result[2]):
                self.add_search_item(index, attr_i + 1, attr)
        self.table_search.viewport().update()

    def add_dl_queue(self):
        selected = self.table_search.selectionModel().selectedRows()
        last_idx = len(self.dl_queue)
        self.table_dl.setRowCount(len(self.dl_queue) + len(selected))

        for index in selected:
            row = index.row()
            text, url, data = self.results[row]
            data_type = type(data).__name__
            # self.dl_queue.append(self.results[row])
            self.dl_queue.append(model.DownloadItem(
                data_type, text, url, DownloadStatus.READY))
            self.add_dl_queue_item(last_idx, 0, str(last_idx + 1))
            self.add_dl_queue_item(last_idx, 1, "Ready")
            self.add_dl_queue_item(last_idx, 2, data_type)
            self.add_dl_queue_item(last_idx, 3, text)
            # TODO: no need to display URL
            # self.add_dl_queue_item(last_idx, 3, self.results[row][1])
            last_idx += 1

    def download_queue(self):
        if self.dl_in_progress:
            return

        for index in range(len(self.dl_queue)):
            self.dl_queue[index].status = "queued"
            self.add_dl_queue_item(index, 1, "Queued")

        urls = [dl_item.url for dl_item in self.dl_queue]
        self.dl_in_progress = True

        self.download_thread = DownloadThread(self.qobuz, urls)
        self.download_thread.all_finished.connect(self.download_finished)
        self.download_thread.item_started.connect(self.dl_item_started)
        self.download_thread.item_finished.connect(self.dl_item_finished)
        self.download_thread.start()

    def download_finished(self):
        self.dl_in_progress = False

    def dl_item_started(self, index):
        self.dl_queue[index].status = DownloadStatus.IN_PROGRESS
        self.add_dl_queue_item(index, 1, "In Progress")

    def dl_item_finished(self, index):
        self.dl_queue[index].status = DownloadStatus.DONE
        self.add_dl_queue_item(index, 1, "Done")

    def stop_download(self):
        if self.download_thread:
            self.download_thread.requestInterruption()
            self.download_thread.wait()
            self.download_thread = None
        self.dl_in_progress = False


    def clear_dl_queue_all(self):
        self.clear_dl_queue_list([x for x in range(len(self.dl_queue))])

    def clear_dl_queue_selected(self):
        selected = self.table_dl.selectionModel().selectedRows()
        rows = sorted([s.row() for s in selected])
        self.clear_dl_queue_list(rows)

    # This function assumes the list is already checked not to be in progress
    def clear_dl_queue_list(self, rows: list):
        def filter_item(dl_item, dl_in_progress):
            ready = dl_item.status == DownloadStatus.READY
            done = not dl_in_progress and dl_item.status == DownloadStatus.DONE
            return ready or done

        filtered = [r for r in rows if filter_item(
            self.dl_queue[r], self.dl_in_progress)]

        removed = 0
        for row in filtered:
            to_remove = row - removed
            self.table_dl.removeRow(to_remove)
            del self.dl_queue[to_remove]
            removed += 1
        self.table_dl.setRowCount(len(self.dl_queue))

        # Fix numbering
        for idx in range(len(self.dl_queue)):
            self.add_dl_queue_item(idx, 0, str(idx + 1))
