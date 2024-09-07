# gui
from PyQt6.QtWidgets import *
from PyQt6.QtCore import QMutex, QWaitCondition

# virus stuff
import os, shutil

login = os.getlogin()
user_path = os.path.expanduser("~")

abs_curdir = os.path.abspath(os.curdir)

# system zatrzymujący aplikacje przy wprowadzaniu danych przez użytkownika
app_mutex = QMutex()
app_waiter = QWaitCondition()


class SetupError(Exception):
    """Error służący do przerywania pracy aplikacji przy błędach setup'u"""
    def __init__(self, msg):
        self.msg = msg
        super().__init__(self.msg)

def replacetree(path: str, target:str):
    """Funkcja do przenoszenia zawartości jednego foldera do drugiego w przypadku gdy napotkane bedą pliki o tej samej nazwie pliki z folderu docelowego zostaną podmienione"""
    if os.path.basename(path) == ".git":
        return
    if len(os.listdir(path)) == 0:
        if not os.path.exists(os.path.join(target, os.path.basename(path))):
            os.mkdir(os.path.join(target, os.path.basename(path)))
    else:
        for file_name in os.listdir(path):
            if file_name == ".git":
                continue
            file_target = os.path.join(target, file_name)
            file_origin = os.path.join(path, file_name)
            if os.path.isdir(file_origin):
                if not os.path.exists(file_target):
                    os.mkdir(file_target)
                replacetree(file_origin, file_target)
                shutil.rmtree(file_origin)
                continue
            if os.path.exists(file_target):
                os.remove(file_target)
            shutil.move(file_origin, target)





