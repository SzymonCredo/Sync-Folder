from PyQt6.QtWidgets import *
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot, QEventLoop, QWaitCondition

# virus stuff
import os, shutil, ctypes

# git
import git
import paramiko

# json
import json

import datetime

from globals import (
    app_mutex, app_waiter,
    login, abs_curdir,
    SetupError,
    replacetree, user_path
)

class Program(QObject):
    progress_info = pyqtSignal(str) # sends information to gui about current
    finished = pyqtSignal() # let gui know method finished its action (hides loading)

    show_commit = pyqtSignal(git.Commit) # display commit in gui

    # alert windows
    alert = pyqtSignal(QMessageBox.Icon, str, str, list)
    ask_path = pyqtSignal(str, bool)
    text_alert = pyqtSignal(str, str, str)
    close_app = pyqtSignal()

    # custom window for displaying public key for user
    ssh_pub_display = pyqtSignal(str, str, str)

    def __init__(self):
        super().__init__()
        self.set_up_finished = False
        self.json_info = {}
        self.origin_path = self.json_info["origin_path"] = ""
        self.repository_path = self.json_info["repository_path"] = ""

        self.repos: git.Repo
        self.gui_response = None



    @pyqtSlot()
    def main(self):
        try:
            if not os.path.exists(os.path.join(abs_curdir, "paths.json")):
                try:
                    self.progress_info.emit("Konfiguruje Chmurę")
                    self.origin_setup()
                    self.progress_info.emit("Konfiguruje klucze dostępu")
                    self.ssh_setup()
                    self.progress_info.emit("Konfiguruje synchronizowany folder")
                    self.git_repository_setup()
                    self.progress_info.emit("Zapisuje...")
                    with open("paths.json", "w") as paths:
                        json.dump(self.json_info, paths)
                except SetupError as e:
                    self.alert.emit(QMessageBox.Icon.Critical, "Problem przy konfigurowaniu aplikacji", e.msg, [QMessageBox.StandardButton.Ok])
                    app_mutex.lock()
                    app_waiter.wait(app_mutex)
                    app_mutex.unlock()
                    self.close_app.emit()
                    return
            else:
                with open(os.path.join(abs_curdir, "paths.json")) as File:
                    self.json_info = json.load(File)

                    self.repository_path = self.json_info["repository_path"]
                    self.origin_path = self.json_info["origin_path"]

                # self.repos.git.config('core.sshCommand', f'ssh -i {self.ssh_key}')
                self.progress_info.emit("Otwieram folder")
                self.repos = git.repo.Repo(self.repository_path)
            self.set_up_finished = True
            print("Otwarto Repozytorium")
            self.pull()
        # except Exception as e:
        #     self.alert.emit(QMessageBox.Icon.Critical, "Napotkano niespodziewany błąd", str(e), [QMessageBox.StandardButton.Ok])
        finally:
            pass # ułatwia komentowanie informacji o nieprzewidzianym błędzie

    # setup methods
    def origin_setup(self):
        self.text_alert.emit("Ścieżka do chmury", "Podaj ścieżkę do folderu w chmurze", "")
        app_mutex.lock()
        app_waiter.wait(app_mutex)
        app_mutex.unlock()
        if self.gui_response:
            self.origin_path = self.json_info["origin_path"] = self.gui_response
        else:
            raise SetupError("Nie podano ścieżki do chmury")

    def ssh_setup(self):
        ssh_dir = os.path.expanduser("~/.ssh")
        if not os.path.exists(ssh_dir):  # dose the .ssh directory exists?
            os.mkdir(ssh_dir)  # create it if not
        self.alert.emit(QMessageBox.Icon.Question, "Konfigurowanie kluczy ssh", "Czy potrzebujesz konfiguracji klucza SSH (dostępu)?\nNie jest to konieczne dla publicznego repozytorium chmury",
                        [
                            ("Tak, mam plik klucza RSA", QMessageBox.ButtonRole.YesRole),
                            ("Tak, potrzebuje nowego klucza", QMessageBox.ButtonRole.YesRole, True),
                            ("Nie", QMessageBox.ButtonRole.RejectRole)
                        ])
        app_mutex.lock()
        app_waiter.wait(app_mutex)
        app_mutex.unlock()

        private_key: paramiko.RSAKey
        key_name: str
        if self.gui_response == 0:  # does user have ssh key
            self.ask_path.emit("Wybierz plik prywatnego klucza ssh (koniecznie RSA)", False)
            app_mutex.lock()
            app_waiter.wait(app_mutex)
            app_mutex.unlock()
            if not self.gui_response:
                raise SetupError("Nie podano ścieżki do klucza ssh")

            private_key = paramiko.RSAKey.from_private_key_file(self.gui_response[0], password=None)
            key_name = os.path.basename(self.gui_response[0])
        elif self.gui_response == 1: # user want program to generate a key
            self.text_alert.emit("Nazwa Klucza", "Podaj nazwę dla klucza do stworzenia", "")
            app_mutex.lock()
            app_waiter.wait(app_mutex)
            app_mutex.unlock()
            if not self.gui_response:
                raise SetupError("Nie podano nazwy klucza")
            key_name = self.gui_response

            # Generate the SSH key pair
            self.progress_info.emit("Generuje klucz")
            private_key = paramiko.RSAKey.generate(1024)

            self.ssh_pub_display.emit("Wygenerowano klucze",
                                      "Twoje klucze zostały skonfigurowane\n"
                                      "Oto twój publiczny klucz publiczny (do skonfigurowania w repozytorium w chmurze)",
                                      f"ssh-rsa {private_key.get_base64()}")
            app_mutex.lock()
            app_waiter.wait(app_mutex)
            app_mutex.unlock()
        elif self.gui_response == 2:
            return

        key_path = os.path.join(ssh_dir, key_name)
        # get public key
        public_key = f"ssh-rsa {private_key.get_base64()}"

        # save both files
        private_key.write_private_key_file(key_path)
        with open(key_path + ".pub", "w") as pub:
            pub.write(public_key)


        host = self.origin_path[self.origin_path.index("@")+1:self.origin_path.index(":")]

        config_entry = f"Host {host}\n" +\
                       f"\tIdentityFile {key_path}"
        with open(os.path.join(ssh_dir, "config"), mode="w") as File:
            File.write(config_entry)

    def git_repository_setup(self):
        self.ask_path.emit("Podaj ścieżkę folderu do synchronizacji ", True)
        app_mutex.lock()
        app_waiter.wait(app_mutex)
        app_mutex.unlock()
        if self.gui_response:
            repository_path = self.repository_path = self.json_info["repository_path"] = self.gui_response[0].replace("/", "\\")
            # empty folder if not empty
            if len(os.listdir(repository_path)):
                tmp_folder = os.path.join(abs_curdir, "tmp_world_files")
                git.rmtree(os.path.join(repository_path, ".git"))
                shutil.move(repository_path, tmp_folder)
                ctypes.windll.kernel32.SetFileAttributesW(tmp_folder, 0x02)  # set folder to be hidden
        else:
            raise SetupError("Nie podano ścieżki folderu")

        self.progress_info.emit("Wczytuje folder z chmury")

        try:
            self.repos = git.repo.Repo.clone_from(self.origin_path, repository_path)
        except git.exc.GitError:
            with open(os.path.join(user_path, ".ssh", "known_hosts"), mode="w") as File:
                File.writelines(["github.com ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQCj7ndNxQowgcQnjshcLrqPEiiphnt+VTTvDP6mHBL9j1aNUkY4Ue1gvwnGLVlOhGeYrnZaMgRK6+PKCUXaDbC7qtbW8gIkhL7aGCsOr/C56SJMy/BCZfxd1nWzAOxSDPgVsmerOBYfNqltV9/hWCqBywINIR+5dIg6JTJ72pcEpEjcYgXkE2YEFXV1JHnsKgbLWNlhScqb2UmyRkQyytRLtL+38TGxkxCflmO+5Z8CSSNY7GidjMIZ7Q4zMjA2n1nGrlTDkzwDCsw+wqFPGQA179cnfGWOWRVruj16z6XyvxvjJwbz0wQZ75XK5tKSb7FNyeIEs4TT4jk+S4dhPeAUC5y+bDYirYgM4GC7uEnztnZyaVWQ7B381AK4Qdrwt51ZqExKbQpTUNn+EjqoTwvqNj4kqx5QUCI0ThS/YkOxJCXmPUWZbhjpCg56i+2aB6CmK2JGhn57K5mj0MNdBXA4/WnwH6XoPWJzK5Nyu2zB3nAZp+S5hpQs+p1vN1/wsjk="])
            self.repos = git.repo.Repo.clone_from(self.origin_path, repository_path)

        # self.repos.git.config('core.sshCommand', f'ssh -i {self.}')


        # copy moved files if there are any
        if os.path.exists(os.path.join(abs_curdir, "tmp_world_files")):
            replacetree(os.path.join(abs_curdir, "tmp_world_files"), repository_path)
            shutil.rmtree(os.path.join(abs_curdir, "tmp_world_files"), ignore_errors=True)

    # app actions
    @pyqtSlot()
    def pull(self):
        self.progress_info.emit("Wczytuje z chmury")
        self.repos.remote("origin").fetch()
        remote_branches = [ref.name for ref in self.repos.refs if ref.name.startswith('origin/')]
        if not remote_branches:
            if not self.repos.head.is_valid():
                self.repos.index.commit("Initial Commit")
            new_head = self.repos.create_head("master")
            new_head.checkout()

            self.repos.remote("origin").push(new_head)

        current_branch = self.repos.active_branch.name

        if remote_branches:
            # Compare the local branch with the remote branch
            local_commit = self.repos.commit(current_branch)
            remote_commit = self.repos.commit(f'origin/{current_branch}')

            if self.repos.is_dirty() and local_commit != remote_commit:
                self.alert.emit(QMessageBox.Icon.Critical, "Konflikt zmian",
                                "Zmiany w chmurze wchodzą w konflikt z nie zapisanymi zmianami na twoim komputerze.\n" +
                                '\tWybranie opcji "Wczytaj" spowoduje usunięcie wszystkich zmian na twoim komputerze i nadpisanie ich zmianami z chmury\n' +
                                '\tWybranie opcji "Zapisz" spowoduje zignorowanie zmian z chmury i nadpisanie ich zmianami z twojego komputera',
                                [
                                    ("Zapisz", QMessageBox.ButtonRole.YesRole),
                                    ("Wczytaj", QMessageBox.ButtonRole.YesRole),
                                    ("Anuluj", QMessageBox.ButtonRole.RejectRole)
                                ])
                app_mutex.lock()
                app_waiter.wait(app_mutex)
                app_mutex.unlock()
                if self.gui_response == 0:
                    print("Wybrano zapisanie lokalnych zmian")
                    self.commit()
                elif self.gui_response != 1:
                    print("Przerwano wczytywanie")
                    self.finished.emit()
                    return
                else:
                    print("Wybrano usunięcie lokalnych zmian")

        self.repos.git.reset('--hard', 'HEAD')
        self.repos.git.clean("-fd")

        # Force the checkout to the current branch, discarding local changes
        branch = self.repos.active_branch.name

        self.repos.git.checkout(branch)
        self.repos.git.reset('--hard', f'origin/{branch}')

        print("Wczytano zapis z chmury\n" + self.repos.head.commit.message)
        self.show_commit.emit(self.repos.head.commit)

    @pyqtSlot()
    def commit(self):
        self.progress_info.emit("Rozpoczynam zapisywanie")
        if self.repos.is_dirty(untracked_files=True):
            print("Repos is dirty")
            self.alert.emit(QMessageBox.Icon.Warning,"Zapisywanie", 'Czy na pewno chcesz zapisać?', [QMessageBox.StandardButton.Yes, QMessageBox.StandardButton.No])
            app_mutex.lock()
            app_waiter.wait(app_mutex)
            app_mutex.unlock()

            if self.gui_response != 0: # przerwano wczytywanie
                self.finished.emit()
                return
            # Dodaje wszystko do repozytorium
            self.repos.git.add(A=True)
            print("Tworze Commit")
            self.repos.index.commit(f"User: {login}, {datetime.datetime.now().strftime('%H:%M %d.%m.%Y')}")
            print("Wysyłam do remote'a")
            if self.repos.active_branch.tracking_branch() is None:
                print("Setting upstream for 'master' to 'origin/master'")
                self.repos.active_branch.set_tracking_branch(self.repos.remote("origin").refs.master)
            self.repos.remote("origin").push(force=True)
            self.show_commit.emit(self.repos.head.commit)
        else:
            self.alert.emit(QMessageBox.Icon.Critical, "Błąd zapisu", "Brak zmian do zapisania", [QMessageBox.StandardButton.Ok])
            app_mutex.lock()
            app_waiter.wait(app_mutex)
            app_mutex.unlock()
            self.finished.emit()
            return


