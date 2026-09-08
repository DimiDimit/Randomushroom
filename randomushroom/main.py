import json
import os
import shutil
import socket
import subprocess
import sys
import threading
from pathlib import Path

from PySide6 import QtWidgets, QtGui

from randomushroom.classes import GameManager, FilePatcher
from randomushroom.constants import *

def main():
    path = None
    # path = Path(path/to/your/game)

    if path is None:
        app = QtWidgets.QApplication(sys.argv)

        QtWidgets.QMessageBox.information(
            None,
            "Find your Mushroom Age Executable",
            "yo this is your reminder to uncomment the 'path' variable in main.py's main() function. ik it kinda sucks but until literally 5 minutes ago i just had my own game path sitting at the top of the file. just make sure not to include that line in your commits lmao. i'll make a proper GUI later i promise. anyway the program is closing now byeeee.",
        )

        sys.exit()

    app = QtWidgets.QApplication(sys.argv)

    if os.name == 'nt':
        app.setStyle('Fusion')

    app_icon = QtGui.QIcon(str(FILES_DIR / APP_ICON))
    app.setWindowIcon(app_icon)

    program = MainProgram(app, path)
    program.show()

    sys.exit(app.exec())

class MainProgram(QtWidgets.QMainWindow):
    server_host = "127.0.0.1"
    server_port = 55554

    def __init__(self, parent, game_directory):
        super().__init__()

        self.game_directory = game_directory.parent
        self.game_executable = game_directory
        self.game_running = False
        self.server_running = False

        self.file_patcher = FilePatcher()
        self.game_manager = GameManager()

        main = QtWidgets.QWidget()
        layout = QtWidgets.QGridLayout(main)
        self.setCentralWidget(main)

        go_button = QtWidgets.QPushButton(self.tr("Launch Game!"))
        go_button.clicked.connect(self.start_randomized_game)
        layout.addWidget(go_button, 0, 0)

        go_button = QtWidgets.QPushButton(self.tr("Clean Directory"))
        go_button.clicked.connect(self.clean_directory)
        layout.addWidget(go_button, 1, 0)

    def start_randomized_game(self):
        if self.game_running:
            return

        self.file_patcher.set_root(self.game_directory)
        self.game_manager.build_tracker(self.game_directory)

        try_patch = self.apply_patch()
        match try_patch:
            case "not an exe":
                print("not an exe file") # TODO: proper error handling
            case "invalid architecture":
                print("invalid architecture")
            case _:
                if not self.server_running:
                    self.server_running = True
                    server_thread = threading.Thread(target = self.begin_tcp_server)
                    server_thread.daemon = True
                    server_thread.start()

                    client_thread = threading.Thread(target = self.begin_client)
                    client_thread.daemon = True
                    client_thread.start()

                game_thread = threading.Thread(target = self.launch_game)
                game_thread.daemon = True
                game_thread.start()

    def clean_directory(self):
        if self.game_running:
            return

        files_to_remove = [
            self.game_directory / "randomushroom.asi",
            self.game_directory / "randomushroom.pdb",
        ]

        for file_path in files_to_remove:
            if file_path.exists(): file_path.unlink()

        folders_to_remove = [
            self.game_directory / "update",
            self.game_directory / "data" / "objects" / "!!!!!!modded",
        ]

        for dir_path in folders_to_remove:
            if dir_path.exists():
                for item in sorted(dir_path.rglob("*"), reverse = True):
                    if item.is_file():  item.unlink()
                    elif item.is_dir(): item.rmdir()

                dir_path.rmdir()

    
    def begin_tcp_server(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((self.server_host, self.server_port))

            s.listen(5)

            print(f"tcp server started")
            while True:
                c, addr = s.accept()

                print(f"client connected at {addr}")

    def begin_client(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            try:
                client_socket.connect((self.server_host, self.server_port))
                print(f"rando client successfully connected!")

                self.client = RandoClient(self.game_manager, client_socket)
                command_dict = {
                    # signals sent from the game
                    "game_begin_task": self.client.on_begin_task,
                    "game_task_complete": self.client.on_task_complete,
                    "game_object_collected": self.client.on_object_collected,
                }

                def send_size_prefixed_data_chunk(self, command, args): # TODO: debug later
                    json_payload = json.dumps({"command": command, "args": args})
                    payload = bytearray(len(json_payload).to_bytes(4, 'big'))
                    payload.extend(json_payload.encode("utf-8"))
                    # TODO: actually send the payload
                self.client.send_payload = send_size_prefixed_data_chunk

                def receive_data_chunk(size):
                    chunk = bytearray()
                    while len(chunk) < size:
                        chunk.extend(client_socket.recv(size - len(chunk)))
                    return chunk

                while True:
                    data_size = int.from_bytes(receive_data_chunk(4), 'big')
                    payload = receive_data_chunk(data_size)
                    data = json.loads(payload)

                    print(f"rando client received payload {data}")
                    if data.get("command") in command_dict:
                        command_dict[data["command"]](self.client, *data.get("args", []))

            except ConnectionRefusedError:
                print("rando client refused to connect")
            except socket.timeout:
                print("rando client timed out")

    def apply_patch(self):
        with open(self.game_executable, "rb") as game_exe:
            header = game_exe.read(2)
            if header != b"MZ":
                return "not an exe"
            else:
                game_exe.seek(60)
                header_offset = int.from_bytes(game_exe.read(4), 'little')

                game_exe.seek(header_offset + 4)
                machine = int.from_bytes(game_exe.read(2), 'little')

                match machine:
                    case 0x014c: arch = "i686"
                    case 0x8664: arch = "x86_64"
                    case _: return "invalid architecture"

        print(f"{arch} EXE detected")

        shutil.copy(
            str(FILES_DIR / "plugin" / arch / "randomushroom.asi"),
            str(self.game_directory),
        )
        pdb_path = FILES_DIR / "plugin" / arch / "randomushroom.pdb"
        if pdb_path.exists():
            shutil.copy(
                str(pdb_path),
                str(self.game_directory),
            )

        for level_str, obj_id in list(filter(lambda x: x[0].endswith("bonus_id"), self.game_manager.bonus_dict.items())):
            self.file_patcher.replace_level_object_image(
                lvl_name = level_str.removesuffix("_bonus_id"),
                obj_id   = obj_id,
                new_img  = None, # TODO: get this info out of AP
            )

    def launch_game(self):
        self.game_running = True
        subprocess.run(
            [str(self.game_executable)],
            cwd = str(self.game_directory),
        )
        self.game_running = False

class RandoClient:
    def __init__(self, game_manager, tcp_client_socket):
        self.game_manager = game_manager
        self.tcp_client_socket = tcp_client_socket


    # signals received from game
    def on_begin_task(self, chapter, task_id):
        task = LEVEL_STRING.format(chapter + 1, task_id + 1)

        if self.game_manager.check_if_task_available(task):
            items = self.game_manager.check_task_gates(task)
            self.send_gate(items)
    
    def on_task_complete(self, chapter, task_id):
        task = LEVEL_STRING.format(chapter + 1, task_id + 1)

        if self.game_manager.complete_task(task):
            self.send_check(task)

            if self.game_manager.complete_quest(task):
                quest_item = self.game_manager.get_quest_name(task)
                self.send_item_notification(quest_item)
                self.send_quest_to_tracker(quest_item)

    def on_object_collected(self, chapter, task_id, object_id): 
        task = LEVEL_STRING.format(chapter + 1, task_id + 1)

        if self.game_manager.collect_task_item(task, object_id):
            self.send_check(f"{task}_bonus")

    # signals sent to game
    def send_gate(self, items):
        self.send_payload("rand_main_menu", [])
        self.send_payload("rand_display_text", [f"You cannot play that task right now!\nYou need: {items}"]) # TODO: test and improve

    def send_item_notification(self, item):
        self.send_payload("rand_display_text", [f"You received {item}!"]) # TODO: test and improve


    # signals received from AP
    def on_receive_check(self, check): # TODO: receive from AP
        ... # TODO: convert signal into self.receive_item call

    # signals sent to AP
    def send_check(self, check):
        ... # TODO: send signal to AP

    def send_quest_to_tracker(self, quest):
        ... # TODO: send signal to AP


    # helper functions
    def receive_item(self, item):
        if self.game_manager.receive_item(item):
            self.send_item_notification(item)
