import glob
import sys
import os
from collections import namedtuple

from PyQt5.QtCore import Qt, QObject
from PyQt5.QtGui import QTextCursor, QKeyEvent, QColor, QBrush
from PyQt5.QtCore import pyqtSignal, pyqtSlot, QThread
from PyQt5 import QtWidgets
from qt_material import apply_stylesheet

from qobuz_dl.core import QobuzDL, QUALITIES

import model
from model import DownloadStatus


def remove_leftovers(directory):
    print(f"remove_leftovers {directory}")
    directory = os.path.join(directory, "**", ".*.tmp")
    for i in glob.glob(directory, recursive=True):
        try:
            os.remove(i)
        except Exception as e:
            print(f"could not delete file {e}")
        except:  # noqa
            print("could not delete file")
            # pass


class EmittingStream(QObject):
    textWritten = pyqtSignal(str)

    def write(self, text):
        self.textWritten.emit(str(text))


class DownloadThread(QThread):
    item_started = pyqtSignal(int)
    item_finished = pyqtSignal(int)
    all_finished = pyqtSignal()

    def __init__(self, qobuz, urls):
        super().__init__()
        self.qobuz = qobuz
        self.urls = urls
        self.setTerminationEnabled(True)

    def run(self):
        if not self.urls or not isinstance(self.urls, list):
            # logger.info(f"{OFF}Nothing to download")
            print(f"Nothing to download")
        else:
            self._download_urls()
        self.all_finished.emit()

    def _download_urls(self):
        for index in range(len(self.urls)):
            interrupt = self.isInterruptionRequested()
            print(f'Interrupt requested: {interrupt}')
            if interrupt:
                break
            self.item_started.emit(index)
            self._handle_url(self.urls[index])
            self.item_finished.emit(index)
        # self.qobuz.download_list_of_urls(self.urls)

    def _handle_url(self, url):
        if "last.fm" in url:
            self.qobuz.download_lastfm_pl(url)
        elif os.path.isfile(url):
            self.qobuz.download_from_txt_file(url)
        else:
            self.qobuz.handle_url(url)


class MainView(QtWidgets.QWidget):
    def __init__(self, qobuz) -> None:
        super().__init__()
        self.qobuz = qobuz
        self.init_view()
        self.setMinimumSize(800, 620)
        self.setWindowTitle("Qobuz Downloader")
        self.results = []
        # List of DownloadItems
        self.dl_queue = []
        self.dl_in_progress = False
        self.download_thread = None

        # TODO: this is temporary until downloader thread is fixed
        # remove_leftovers(self.qobuz.directory)

    def __info__(self, msg):
        QtWidgets.QMessageBox.information(self, 'Info', msg, QtWidgets.QMessageBox.Yes)

    def __output__(self, text):
        cursor = self.print_text_edit.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(text)
        self.print_text_edit.setTextCursor(cursor)
        self.print_text_edit.ensureCursorVisible()

    def init_view(self):
        self.create_view_navigation_layout()

        self.create_layout_search()
        self.create_layout_download()

        main_grid = QtWidgets.QHBoxLayout(self)
        main_grid.addWidget(self.views)
        main_grid.addWidget(self.frame_search)
        main_grid.addWidget(self.frame_download)
        self.frame_download.hide()

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
        self.frame_search.show()

    def show_dl_view(self):
        self.frame_search.hide()
        self.frame_download.show()

    def show_cfg_view(self):
        print("show_cfg_view")
        # pass

    def create_layout_search(self):
        self.line_search = QtWidgets.QLineEdit()
        self.btn_search = QtWidgets.QPushButton("Search")
        self.btn_add_dl_queue = QtWidgets.QPushButton("Add to Download")
        self.comb_search_type = QtWidgets.QComboBox()
        # self.comb_quality = QtWidgets.QComboBox()

        # Supported types for search
        self.search_types = [model.Album, model.Artist, model.Track, model.Playlist]
        for item in self.search_types:
            self.comb_search_type.addItem(item.__name__, item)
        self.comb_search_type.setCurrentText("Album")

        # TODO: make connection between selection and data
        # for _, val in QUALITIES.items():
        #     self.comb_quality.addItem(val)
        # self.comb_quality.setCurrentText(QUALITIES[self.qobuz.quality])

        # init table
        column_names = ["#", "Description", "URL"]
        self.table_search = self.create_search_table(column_names)

        # print
        self.print_text_edit = QtWidgets.QTextEdit()
        self.print_text_edit.setReadOnly(True)
        self.print_text_edit.setFixedHeight(100)

        # layout
        line_grid = QtWidgets.QHBoxLayout()
        line_grid.addWidget(self.comb_search_type)
        line_grid.addWidget(self.line_search)
        line_grid.addWidget(self.btn_search)

        line_grid_2 = QtWidgets.QHBoxLayout()
        # line_grid_2.addWidget(QtWidgets.QLabel("QUALITY:"))
        # line_grid_2.addWidget(self.comb_quality)
        line_grid_2.addStretch(4)
        line_grid_2.addWidget(self.btn_add_dl_queue)

        search_view = QtWidgets.QVBoxLayout()
        search_view.addLayout(line_grid)
        search_view.addWidget(self.table_search)
        search_view.addLayout(line_grid_2)
        search_view.addWidget(self.print_text_edit)

        self.frame_search = QtWidgets.QFrame()
        self.frame_search.setLayout(search_view)

        # connect
        self.btn_search.clicked.connect(self.search)
        self.btn_add_dl_queue.clicked.connect(self.add_dl_queue)
        self.line_search.returnPressed.connect(self.search)

    def create_layout_download(self):
        # init table
        column_names = ["#", "Status", "Type", "Description"]
        self.table_dl = self.create_search_table(column_names)

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

    def search(self):
        self.s_type = self.comb_search_type.currentData()
        s_type_str = self.s_type.__name__.lower()
        query = self.line_search.text()
        if len(query) == 0:
            return
        results_raw = self.qobuz.search_by_type(query, s_type_str)
        self.results.clear()
        for result in results_raw:
            text = result["text"]
            data = model.parse_str(s_type_str, text)
            url = result["url"]
            self.results.append((text, url, data))

        self.set_search_result(self.s_type, self.results)

    def create_search_table(self, column_names) -> QtWidgets.QTableWidget:
        table = QtWidgets.QTableWidget()
        table.setColumnCount(len(column_names))
        table.setRowCount(0)
        table.setShowGrid(False)
        table.verticalHeader().setVisible(False)
        table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        table.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        table.horizontalHeader().setStretchLastSection(True)
        table.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
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
        self.download_thread.setTerminationEnabled(True)
        self.download_thread.start()

    def download_finished(self):
        print('Finshed downloading')
        # TODO: change row colors back to original
        self.dl_in_progress = False

    def dl_item_started(self, index):
        self.dl_queue[index].status = DownloadStatus.IN_PROGRESS
        self.add_dl_queue_item(index, 1, "In Progress")

    def dl_item_finished(self, index):
        self.dl_queue[index].status = DownloadStatus.DONE
        self.add_dl_queue_item(index, 1, "Done")

    def stop_download(self):
        # TODO: implement
        if self.download_thread:
            # TODO: terminating threads is unsafe and leaves the files
            # in a locked state, this is a temporary solution!
            print('stop_download')
            self.download_thread.terminate()
            self.download_thread.wait()
            print('terminated waited')
            self.download_thread = None
        self.dl_in_progress = False


    def clear_dl_queue_all(self):
        # self.dl_queue.clear()
        # self.table_dl.setRowCount(0)
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


def start_gui(qobuz):
    app = QtWidgets.QApplication(sys.argv)
    apply_stylesheet(app, theme='theme.xml')

    # TODO make a login window
    window = MainView(qobuz)
    window.show()
    # window.checkLogin()

    app.exec_()


# TODO: create settings that will save the input
def login():
    # email = input("E-mail: ")
    # password = input("Password: ")

    email = "kobuzmisilevi@gmail.com"
    password = "Kobuz777!"
    qobuz = QobuzDL()
    qobuz.get_tokens() # get 'app_id' and 'secrets' attrs
    qobuz.initialize_client(email, password, qobuz.app_id, qobuz.secrets)
    return qobuz


if __name__ == '__main__':
    qobuz = login()
    start_gui(qobuz)
