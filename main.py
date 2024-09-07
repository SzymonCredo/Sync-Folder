# gui
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QThread, QMutex, QWaitCondition

import sys, os

# my files
from Program import Program
from MainWindow import MainWindow

app = QApplication(sys.argv)


program = Program()
window = MainWindow(program)

# show in app signals
program.progress_info.connect(window.display_loading_message)
program.show_commit.connect(window.commit_display)

# popup alerts signals
program.alert.connect(window.display_alert)
program.text_alert.connect(window.text_alert)
program.ask_path.connect(window.path_alert)
program.ssh_pub_display.connect(window.ssh_pub_display)

# app unable to continue signal
program.close_app.connect(window.close)

# method finished signal
program.finished.connect(window.hide_loading)

# button binds
window.pull.connect(program.pull)
window.commit.connect(program.commit)

thread = QThread()
program.moveToThread(thread)

thread.started.connect(program.main)
window.show()
thread.start()
app.exec()


