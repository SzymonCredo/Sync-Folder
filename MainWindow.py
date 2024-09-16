import typing

from PyQt6.QtWidgets import *
from PyQt6.QtCore import pyqtSlot, pyqtSignal, QSize, Qt
from PyQt6.QtGui import QCloseEvent, QMovie, QFont

from git import Commit

from os import path

from globals import abs_curdir, app_waiter

from Program import Program

class MainWindow(QMainWindow):
    commit = pyqtSignal()
    pull = pyqtSignal()

    alert_response = pyqtSignal(bool)

    def __init__(self, program):
        self.program: Program = program
        super().__init__()
        self.setWindowTitle('Synchronizacja folderu')
        self.setMinimumWidth(300)

        widget = QWidget()

        # main layout <body>
        main_layout = QGridLayout()
        widget.setLayout(main_layout)

        # loading <main>
        # will be displayed during every loading
        self.loading_main = QWidget()
        layout = QVBoxLayout(self.loading_main)
        main_layout.addWidget(self.loading_main, 0, 0)

        self.loading_animation = QMovie(path.join(abs_curdir, "loading.gif"))
        self.loading_animation.setScaledSize(QSize(50, 50))

        indicator = QLabel()
        indicator.setAlignment(Qt.AlignmentFlag.AlignCenter)
        indicator.setMovie(self.loading_animation)
        layout.addWidget(indicator)
        self.loading_animation.start()

        self.alert = QLabel()
        self.alert.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.alert)

        # normal <main>
        # will be displayed after setup
        self.normal_main = QWidget()
        layout = QVBoxLayout(self.normal_main)
        layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        main_layout.addWidget(self.normal_main, 0, 0)

        # <footer>
        footer = QWidget()
        layout = QHBoxLayout(footer)
        main_layout.addWidget(footer, 1, 0)

        self.pull_button = QPushButton("Wczytaj", footer)
        layout.addWidget(self.pull_button)

        self.commit_button = QPushButton('Zapisz', footer)
        layout.addWidget(self.commit_button)

        self.pull_button.clicked.connect(self.pull.emit)
        self.pull_button.clicked.connect(self.show_loading)
        self.commit_button.clicked.connect(self.commit.emit)
        self.commit_button.clicked.connect(self.show_loading)

        self.setCentralWidget(widget)
        self.show_loading()

    # switch app layout (loading/normal)
    def show_loading(self):
        self.pull_button.setEnabled(False)
        self.commit_button.setEnabled(False)
        self.loading_animation.start()
        self.loading_main.show()
        self.normal_main.hide()

    def hide_loading(self):
        self.pull_button.setEnabled(True)
        self.commit_button.setEnabled(True)
        self.loading_animation.stop()
        self.loading_main.hide()
        self.normal_main.show()

    # display in main window signal
    @pyqtSlot(str)
    def display_loading_message(self, tekst: str):
        self.alert.setText(tekst)

    @pyqtSlot(Commit)
    def commit_display(self, head:Commit):
        layout = self.normal_main.layout()
        self.normal_main.children().clear()
        for i in range(layout.count()):
            layout.itemAt(i).widget().deleteLater()
        commit_message = head.message.split(",")[0]

        layout.addWidget(QLabel("Obecny Zapis"))
        layout.addWidget(QLabel("Autor: "+commit_message))
        layout.addWidget(QLabel("Data: "+ head.committed_datetime.strftime('%H:%M %d.%m.%Y')))

        if self.program.repos.is_dirty(untracked_files=True):
            save_message = QLabel("W folderze są niezapisane zmiany")
            save_message.setStyleSheet("color:red;")
        else:
            save_message = QLabel("Wszystkie zmiany są zapisane")
            save_message.setStyleSheet("color:green;")
        layout.addWidget(save_message)
        self.hide_loading()

    # close events
    def closeEvent(self, event:QCloseEvent):
        if self.program.set_up_finished and self.program.repos.is_dirty():
            reply = QMessageBox.warning(self, "Świat posiada niezapisane zmiany",
                                        "Wykryto niezapisane zmiany może to skutkować błędami synchronizacji\n"+
                                        "Zamknięcie aplikacji będzie skutkować odrzuceniem niezapisanych zmian\n"+
                                        "czy na pewno chcesz zamknąć aplikacje?",
                                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                        QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

    # display in separate window
    @pyqtSlot(QMessageBox.Icon, str, str, list)
    def display_alert(self, icon: QMessageBox.Icon, title: str, text: str,
                      buttons: list[QMessageBox.StandardButton | tuple[QPushButton | str, QMessageBox.ButtonRole] | tuple[QPushButton | str, QMessageBox.ButtonRole, bool]]):
        box = QMessageBox(icon, title, text)
        relButtons = []
        for button in buttons:
            if type(button) == QMessageBox.StandardButton:
                if button == QMessageBox.StandardButton.Yes:
                    real_button = box.addButton("Tak", QMessageBox.ButtonRole.YesRole)
                elif button == QMessageBox.StandardButton.No:
                    real_button = box.addButton("Nie", QMessageBox.ButtonRole.NoRole)
                elif button == QMessageBox.StandardButton.Ok:
                    real_button = box.addButton("Ok", QMessageBox.ButtonRole.AcceptRole)
                else:
                    real_button = box.addButton("Anuluj", QMessageBox.ButtonRole.RejectRole)
                relButtons.append(real_button)
                continue
            elif type(button) != QMessageBox.StandardButton:
                real_button = box.addButton(button[0], button[1])
                if len(button) == 3 and button[2]:
                    box.setDefaultButton(real_button)
                relButtons.append(real_button)


        res = box.exec()
        if box.clickedButton():
            self.program.gui_response = relButtons.index(box.clickedButton())
        else:
            self.program.gui_response = None
        app_waiter.wakeAll()

    @pyqtSlot(str, bool)
    def path_alert(self, title: str, dir_mode: bool):
        box = QFileDialog(None, title)
        if dir_mode:
            box.setFileMode(QFileDialog.FileMode.Directory)
        if box.exec():
            self.program.gui_response = box.selectedFiles()
        else:
            self.program.gui_response = []
        app_waiter.wakeAll()



    @pyqtSlot(str, str, str)
    def text_alert(self, title: str, label: str, defvalue: str):
        window = QDialog()
        window.setWindowTitle(title)
        window.setFixedHeight(120)
        window.setMinimumWidth(300)

        layout = QVBoxLayout()
        window.setLayout(layout)

        layout.addWidget(QLabel(label))

        tekst = QLineEdit()
        tekst.setText(defvalue)
        layout.addWidget(tekst)

        buttons = QWidget()
        buttons.setContentsMargins(0, 0, 0, 0)
        b_l = QHBoxLayout()
        buttons.setLayout(b_l)


        b = QPushButton("Ok")
        b.clicked.connect(window.accept)
        b_l.addWidget(b)


        c = QPushButton("Cancel")
        c.clicked.connect(window.reject)
        b_l.addWidget(c)
        layout.addWidget(buttons, alignment=Qt.AlignmentFlag.AlignRight)

        res = window.exec()

        if window.result():
            self.program.gui_response = tekst.text()
        else:
            self.program.gui_response = None
        app_waiter.wakeAll()

    @pyqtSlot(str, str, str)
    def ssh_pub_display(self, title: str, label: str, text: str):
        window = QDialog()
        window.setWindowTitle(title)

        layout = QVBoxLayout()
        window.setLayout(layout)
        layout.addWidget(QLabel(label))
        text_edit = QTextEdit()
        text_edit.setText(text)
        text_edit.setReadOnly(True)
        layout.addWidget(text_edit)

        but = QPushButton("Ok")
        but.clicked.connect(window.close)

        layout.addWidget(but, alignment=Qt.AlignmentFlag.AlignRight)

        window.exec()
        app_waiter.wakeAll()