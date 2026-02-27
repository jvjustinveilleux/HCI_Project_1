import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QTreeView, QPushButton, QSplitter,
                             QListView, QLabel, QFrame, QHeaderView, QSpacerItem, 
                             QSizePolicy, QMessageBox, QInputDialog) # Added QMessageBox and QInputDialog
from PySide6.QtGui import QStandardItemModel, QStandardItem
from PySide6.QtCore import Qt, QSize

from PySide6.QtGui import QIcon, QStandardItem
from PySide6.QtCore import Qt

class SubwayExplorer(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Subway Systems Explorer")
        self.resize(900, 600)

        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels(["Transit Network"])

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        
        self.splitter = QSplitter(Qt.Horizontal)
        
        # station tree nav
        self.tree_view = QTreeView()
        self.tree_view.setIndentation(20) # Increased slightly for better visual nesting
        self.tree_view.setModel(self.model)
        
        #better horizontal scrolling
        self.tree_view.header().setStretchLastSection(False)
        self.tree_view.header().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.tree_view.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        self.tree_view.setEditTriggers(QTreeView.NoEditTriggers)

        self.splitter.addWidget(self.tree_view)

        # station contents
        self.right_container = QWidget()
        self.right_layout = QVBoxLayout(self.right_container)
        
        self.station_label = QLabel("Station: 0")
        self.station_label.setStyleSheet("font-size: 18px; font-weight: bold; padding: 10px;")
        self.station_label.setAlignment(Qt.AlignCenter)
        
        self.content_view = QListView()
        self.content_view.setModel(self.model)
        self.content_view.setViewMode(QListView.IconMode) 
        self.content_view.setSpacing(100)
        self.content_view.setGridSize(QSize(125, 125)) # adjusted the grid size of each content
        self.content_view.setResizeMode(QListView.Adjust)
        
        self.content_view.setEditTriggers(QListView.NoEditTriggers)

        self.right_layout.addWidget(self.station_label)
        self.right_layout.addWidget(self.content_view)
        self.splitter.addWidget(self.right_container)
        
        
        self.splitter.setSizes([270, 630])
        self.main_layout.addWidget(self.splitter)

        # bottom buttons
        self.button_row = QHBoxLayout()
        self.btn_new_station = QPushButton("New Station")
        self.btn_new_train = QPushButton("New Train")
        self.btn_rename = QPushButton("Rename") 
        self.btn_rename.setEnabled(False)
        self.btn_delete = QPushButton("Decomission")
        self.btn_delete.setEnabled(False) #grayed out unless clicked

        self.button_row.addWidget(self.btn_new_station)
        self.button_row.addWidget(self.btn_new_train)
        self.button_row.addWidget(self.btn_rename)
        self.button_row.addWidget(self.btn_delete)
        self.main_layout.addLayout(self.button_row)

        
        self.setup_default_network()
        self.setup_connections()


    def setup_default_network(self):
        #stations 0-5, 3 trains in each one
        station_icon = QIcon("train_station_image.png")  # your station image
        train_icon = QIcon("train_image.png")      # your train image

        parent = self.model.invisibleRootItem()
        for i in range(6):
            station = QStandardItem(f"Station {i}")
            station.setData("station", Qt.UserRole)
            station.setIcon(station_icon)  # <-- add icon
            parent.appendRow(station)
            
            for j in range(1, 4):
                train = QStandardItem(f"Train {i}-{j}")
                train.setData("train", Qt.UserRole)
                train.setIcon(train_icon)  # <-- add icon
                station.appendRow(train)
            
            parent = station#nesting
        
        self.tree_view.expandAll()
        #opens station 0
        self.content_view.setRootIndex(self.model.index(0, 0))

    def setup_connections(self):
        #what is clicked on the left, is shown on the right
        self.tree_view.clicked.connect(self.sync_views)
        self.content_view.clicked.connect(self.enable_delete)

        #new event to see if trains are double clicked
        self.tree_view.doubleClicked.connect(self.show_welcome_message)
        self.content_view.doubleClicked.connect(self.show_welcome_message)
        
        #buttons
        self.btn_new_station.clicked.connect(self.add_station)
        self.btn_new_train.clicked.connect(self.add_train)
        self.btn_rename.clicked.connect(self.rename_item)
        self.btn_delete.clicked.connect(self.delete_item)

    def show_welcome_message(self, index):
        item = self.model.itemFromIndex(index)
        if item.data(Qt.UserRole) == "train":
            msg = QMessageBox(self)
            msg.setWindowTitle("Inside Train")
            msg.setText(f"All Aboard {item.text()}!")
            msg.setIcon(QMessageBox.Information)
            msg.exec()

    def sync_views(self, index):
        item = self.model.itemFromIndex(index)
        if item.data(Qt.UserRole) == "station":
            self.content_view.setRootIndex(index)
            self.station_label.setText(f"Station: \"{item.text()}\"")
        self.enable_delete()

    def enable_delete(self):
        self.btn_delete.setEnabled(True)
        self.btn_rename.setEnabled(True)

    def rename_item(self):
        index = self.content_view.currentIndex() if self.content_view.hasFocus() else self.tree_view.currentIndex()
        if index.isValid():
            item = self.model.itemFromIndex(index)
            
            #do not rename station 0
            if item.text() == "Station 0":
                QMessageBox.warning(self, "Protected", "Station 0 cannot be renamed.")
                return

            new_name, ok = QInputDialog.getText(self, "Rename", "New name:", text=item.text())
            if ok and new_name:
                item.setText(new_name)
                #label updater
                if self.content_view.rootIndex() == index:
                    self.station_label.setText(f"Station: \"{new_name}\"")

    def add_station(self):
        parent_index = self.content_view.rootIndex()
        parent_item = self.model.itemFromIndex(parent_index) or self.model.invisibleRootItem()
        new_station = QStandardItem("New Station")
        new_station.setData("station", Qt.UserRole)
        parent_item.appendRow(new_station)

    def add_train(self):
        parent_index = self.content_view.rootIndex()
        parent_item = self.model.itemFromIndex(parent_index) or self.model.invisibleRootItem()
        new_train = QStandardItem("New Train")
        new_train.setData("train", Qt.UserRole)
        parent_item.appendRow(new_train)

    def delete_item(self):
        #is item clicked
        index = self.content_view.currentIndex() if self.content_view.hasFocus() else self.tree_view.currentIndex()
        if index.isValid():
            item = self.model.itemFromIndex(index)
            #do not dlete station 0
            if item.text() == "Station 0":
                QMessageBox.warning(self, "Protected", "Station 0 cannot be decommissioned.")
                return
            
            self.model.removeRow(index.row(), index.parent())
            self.btn_delete.setEnabled(False)
            self.btn_rename.setEnabled(False)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SubwayExplorer()
    window.show()
    sys.exit(app.exec())