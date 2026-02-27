import sys
import os
import platform
import subprocess
import shutil
from pathlib import Path
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QTreeView, QPushButton, QSplitter,
                             QListView, QLabel, QHeaderView, QMessageBox, QInputDialog)
from PySide6.QtGui import QStandardItemModel, QStandardItem, QIcon
from PySide6.QtCore import Qt, QSize

class SubwayExplorer(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Subway Systems Explorer")
        self.resize(1000, 700)

        
        self.root_path = Path.cwd() / "example_filesystem"
        if not self.root_path.exists():
            self.root_path.mkdir(parents=True, exist_ok=True)

        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels(["Transit Network"])

        self.setup_ui()
        self.load_file_system(self.root_path)
        self.setup_connections()

    def setup_ui(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        self.splitter = QSplitter(Qt.Horizontal)
        
        # Left: Station tree (Navigation Only)
        self.tree_view = QTreeView()
        self.tree_view.setModel(self.model)
        self.tree_view.header().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.tree_view.setEditTriggers(QTreeView.NoEditTriggers)
        self.splitter.addWidget(self.tree_view)

        # Right: Station contents (Action Zone)
        self.right_container = QWidget()
        self.right_layout = QVBoxLayout(self.right_container)
        
        self.station_label = QLabel(f"Hub: {self.root_path.name}")
        self.station_label.setStyleSheet("font-size: 16px; font-weight: bold; padding: 5px; color: #2c3e50;")
        
        self.content_view = QListView()
        self.content_view.setModel(self.model)
        self.content_view.setViewMode(QListView.IconMode) 
        self.content_view.setSpacing(20)
        self.content_view.setGridSize(QSize(130, 130))
        self.content_view.setResizeMode(QListView.Adjust)
        self.content_view.setEditTriggers(QListView.NoEditTriggers)

        self.right_layout.addWidget(self.station_label)
        self.right_layout.addWidget(self.content_view)
        self.splitter.addWidget(self.right_container)
        
        self.splitter.setSizes([300, 700])
        self.main_layout.addWidget(self.splitter)

        # Bottom buttons
        self.button_row = QHBoxLayout()
        self.btn_new_station = QPushButton("New Station")
        self.btn_new_train = QPushButton("New Train")
        self.btn_rename = QPushButton("Rename") 
        self.btn_delete = QPushButton("Decommission")
        
        
        self.btn_rename.setEnabled(False)
        self.btn_delete.setEnabled(False)

        self.button_row.addWidget(self.btn_new_station)
        self.button_row.addWidget(self.btn_new_train)
        self.button_row.addWidget(self.btn_rename)
        self.button_row.addWidget(self.btn_delete)
        self.main_layout.addLayout(self.button_row)

    def load_file_system(self, root_path):
        self.model.clear()
        self.model.setHorizontalHeaderLabels(["Transit Network"])
        root_item = self.model.invisibleRootItem()
        self.populate_branch(root_path, root_item)
        self.tree_view.expandAll()
        self.content_view.setRootIndex(self.model.index(0, 0))

    def populate_branch(self, path, parent_item):
        try:
            entries = sorted(os.scandir(path), key=lambda e: (not e.is_dir(), e.name.lower()))
            for entry in entries:
                if entry.name.startswith('.') or entry.name == ".DS_Store":
                    continue
                
                item = QStandardItem(entry.name)
                item.setData(entry.path, Qt.UserRole + 1)
                
                if entry.is_dir():
                    item.setData("station", Qt.UserRole)
                    item.setIcon(QIcon("train_station_image.png"))
                    parent_item.appendRow(item)
                    self.populate_branch(entry.path, item)
                else:
                    item.setData("train", Qt.UserRole)
                    item.setIcon(QIcon("train_image.png"))
                    parent_item.appendRow(item)
        except PermissionError:
            pass

    def setup_connections(self):
        self.tree_view.clicked.connect(self.navigate_hub)
        
        self.content_view.clicked.connect(self.enable_actions)
        
        #to open station/train 
        self.tree_view.doubleClicked.connect(self.board_train)
        self.content_view.doubleClicked.connect(self.board_train)
        
        # Button Actions
        self.btn_new_station.clicked.connect(self.add_station)
        self.btn_new_train.clicked.connect(self.add_train)
        self.btn_rename.clicked.connect(self.rename_item)
        self.btn_delete.clicked.connect(self.delete_item)

    def navigate_hub(self, index):
        # tree nav on left, shows contents on right
        item = self.model.itemFromIndex(index)
        if item.data(Qt.UserRole) == "station":
            self.content_view.setRootIndex(index)
            self.station_label.setText(f"Hub: \"{item.text()}\"")
        
        self.btn_rename.setEnabled(False)
        self.btn_delete.setEnabled(False)

    def enable_actions(self, index):
        # for last 2 buttons
        self.btn_rename.setEnabled(True)
        self.btn_delete.setEnabled(True)

    def board_train(self, index):
        path = self.model.itemFromIndex(index).data(Qt.UserRole + 1)
        if os.path.isfile(path):
            if platform.system() == "Windows":
                os.startfile(path)
            elif platform.system() == "Darwin":
                subprocess.call(["open", path])
            else:
                subprocess.call(["xdg-open", path])
        else:
            self.content_view.setRootIndex(index)
            self.station_label.setText(f"Hub: \"{os.path.basename(path)}\"")
            #re-gray buttons out because inside new station
            self.btn_rename.setEnabled(False)
            self.btn_delete.setEnabled(False)

    def add_station(self):
        parent_idx = self.content_view.rootIndex()
        parent_path = Path(self.model.itemFromIndex(parent_idx).data(Qt.UserRole + 1)) if parent_idx.isValid() else self.root_path
        parent_item = self.model.itemFromIndex(parent_idx) or self.model.invisibleRootItem()

        name, ok = QInputDialog.getText(self, "New Station", "Enter Station Name:")
        if ok and name:
            new_path = parent_path / name
            try:
                new_path.mkdir()
                item = QStandardItem(name)
                item.setData("station", Qt.UserRole)
                item.setData(str(new_path), Qt.UserRole + 1)
                item.setIcon(QIcon("train_station_image.png"))
                parent_item.appendRow(item)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed: {e}")

    def add_train(self):
        parent_idx = self.content_view.rootIndex()
        parent_path = Path(self.model.itemFromIndex(parent_idx).data(Qt.UserRole + 1)) if parent_idx.isValid() else self.root_path
        parent_item = self.model.itemFromIndex(parent_idx) or self.model.invisibleRootItem()

        name, ok = QInputDialog.getText(self, "New Train", "Enter Train Name:")
        if ok and name:
            new_path = parent_path / name
            try:
                new_path.touch()
                item = QStandardItem(name)
                item.setData("train", Qt.UserRole)
                item.setData(str(new_path), Qt.UserRole + 1)
                item.setIcon(QIcon("train_image.png"))
                parent_item.appendRow(item)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed: {e}")

    def rename_item(self):
        index = self.content_view.currentIndex()
        if not index.isValid(): return
        
        item = self.model.itemFromIndex(index)
        old_path = Path(item.data(Qt.UserRole + 1))
        
        new_name, ok = QInputDialog.getText(self, "Rename", f"Rename '{item.text()}' to:", text=item.text())
        if ok and new_name:
            new_path = old_path.parent / new_name
            try:
                os.rename(old_path, new_path)
                item.setText(new_name)
                item.setData(str(new_path), Qt.UserRole + 1)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Rename failed: {e}")

    def delete_item(self):
        index = self.content_view.currentIndex()
        if not index.isValid(): return
        
        item = self.model.itemFromIndex(index)
        path = Path(item.data(Qt.UserRole + 1))
        
        confirm = QMessageBox.question(self, "Decommission", f"Send {item.text()} to the scrap heap?")
        if confirm == QMessageBox.Yes:
            try:
                if path.is_dir():
                    shutil.rmtree(path)
                else:
                    path.unlink()
                self.model.removeRow(index.row(), index.parent())
                self.btn_rename.setEnabled(False)
                self.btn_delete.setEnabled(False)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SubwayExplorer()
    window.show()
    sys.exit(app.exec())