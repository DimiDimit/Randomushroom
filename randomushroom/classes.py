import itertools
import re
import shutil

from PIL import Image

from randomushroom.constants import *
from randomushroom.key_constants import *


class GameManager:
    def build_tracker(self, game_directory):
        tracker_builder = TrackerBuilder(game_directory)

        self.tracker_dict = tracker_builder.build_tracking_dict() # for checking which tasks are complete and which key items are attained
        self.gate_dict =    tracker_builder.build_gate_dict()     # for checking if a task is allowed to be played at the moment
        self.bonus_dict =   tracker_builder.build_bonus_dict()    # for checking which object IDs give checks, and which tasks give quests

    # returns True if the conditions for playing that task are met, returns False if not
    def check_if_task_available(self, task):
        conditions = self.gate_dict[task]
        for cond in conditions:
            if not self.tracker_dict[cond]: return False
        return True

    # get conditions for task gating
    def check_task_gates(self, task):
        conditions = self.gate_dict[task]
        return conditions

    # modifies task progress. returns True if task was newly completed, returns False if not
    def complete_task(self, task):
        if self.tracker_dict[task]:
            return False

        self.tracker_dict[task] = True
        return True

    # modifies task bonus progress. returns True if bonus was newly obtained, returns False if not, or if item was not a bonus item
    def collect_task_item(self, task, object_id):
        bonus = f"{task}_bonus"

        if bonus in self.tracker_dict:
            if self.tracker_dict[bonus]:
                return False

            bonus_id = self.bonus_dict[f"{bonus}_id"]
            if object_id == bonus_id:
                self.tracker_dict[bonus] = True
                return True
            else:
                return False
        
        return False

    # modifies quest progress. returns quest item name if quest was newly completed, returns False if not, or if task was not a quest giver
    def complete_quest(self, task):
        quest = f"{task}_quest"

        if quest in self.bonus_dict:
            quest_name = self.bonus_dict[quest]
            if self.tracker_dict[quest_name]:
                return False

            self.tracker_dict[quest_name] = True
            return True
        
        return False

    # get the name of a task's quest
    def get_quest_name(self, task):
        quest = f"{task}_quest"
        return self.bonus_dict[quest]

    # modifies key inventory. returns True if item was newly obtained, returns False if not, or if item was junk
    def receive_item(self, item):
        if item in self.tracker_dict:
            if self.tracker_dict[item]:
                return False

            self.tracker_dict[item] = True
            return True
        
        elif item in PROGRESSION_ITEMS:
            for progress_item in PROGRESSION_ITEMS[item]:
                if self.tracker_dict[progress_item]:
                    continue
                
                self.tracker_dict[progress_item] = True
                return True

            return False
        
        return False

class TrackerBuilder:
    def __init__(self, game_directory):
        self.file_helper = FileHelper()
        self.file_helper.set_root(game_directory / "data")

        self._gather_languages()
        self._gather_tasks()
        self._gather_task_strings()
        self._gather_bonus_checks()

    def _gather_languages(self):
        self.languages = set()

        def add_lang(lang_strings):
            self.languages.update(lang_strings.split(","))

        def add_default_lang(lang):
            self.default_lang = lang
            self.languages.add(lang)

        self.file_helper.process_script(
                file = f"settings.ini",
                commands = {
                    r"languages={(.+)}": add_lang,
                    r"lang=(.+)": add_default_lang,
                },
                encoding = 'utf-8',
            )

    def _gather_tasks(self):
        self.all_tasks = []

        def count_chapter(chapter_id):
            self.chapter_counter = chapter_id + 1
            self.task_counter = 1

        def count_task():
            self.all_tasks.append((self.chapter_counter, self.task_counter))
            self.task_counter += 1

        self.file_helper.process_script(
            file = f"comics_{self.default_lang}.txt",
            commands = {
                r"stage\((\d+)\)": count_chapter,
                r"task=.+": count_task,
            },
        )
    
    def _gather_task_strings(self):
        self.task_names = {}

        def add_task_string(string):
            if self.all_tasks[self.current_task] not in self.task_names:
                self.task_names[self.all_tasks[self.current_task]] = {}
            
            self.task_names[self.all_tasks[self.current_task]][self.current_lang] = string
            self.current_task += 1

        for lang in self.languages:
            self.current_task = 0
            self.current_lang = lang

            self.file_helper.process_script(
                file = f"comics_{lang}.txt",
                commands = {
                    r"task=(.+)": add_task_string,
                },
            )
    
    def _gather_bonus_checks(self):
        self.bonus_checks = []

        def check_gamemode(mode):
            if mode not in [0]:
                self.process = False

        def check_selectmode(mode):
            if mode not in [1, 2]:
                self.process = False
        
        def has_silhouettes():
            self.has_silhouettes = True

        for task in self.all_tasks:
            self.process = True
            self.has_silhouettes = False

            self.file_helper.process_script(
                file = LEVEL_STRING.format(*task) + ".lvl",
                commands = {
                    r"gamemode=(\d+)": check_gamemode,
                    r"selectmode=(\d+)": check_selectmode,
                    r"ar_ids\d+=\d+": has_silhouettes,
                },
                encoding = 'utf-8',
            )

            if self.process and self.has_silhouettes:
                self.bonus_checks.append(task)
    
    def build_tracking_dict(self):
        output = {}

        for check in self.all_tasks:
            output[LEVEL_STRING.format(*check)] = False

        for check in self.bonus_checks:
            output[LEVEL_STRING.format(*check) + "_bonus"] = False

        items = KEY_ITEMS | KEY_QUESTS | KEY_PHONE_NUMBERS
        for item in items:
            output[item] = False

        return output

    def build_gate_dict(self):
        output = {}

        gatekeepers = KEY_ITEMS | KEY_QUESTS | KEY_PHONE_NUMBERS

        for period, period_dict in TIME_PERIODS.items():
            gates = []
            for chapter in period_dict["chapters"]:
                for task in self.all_tasks:
                    if chapter != task[0]: continue

                    for gatekeeper, gatekeeper_dict in gatekeepers.items():
                        if task in gatekeeper_dict["gates"]:
                            gates.append(gatekeeper)

                    output[LEVEL_STRING.format(*task)] = list(gates)

        return output

    def build_bonus_dict(self):
        output = {}

        bonus_check_ids = {}

        def add_item_id(item_id):
            self.current_id_set.add(item_id)

        for check in self.bonus_checks:
            self.current_id_set = set()

            self.file_helper.process_script(
                file = LEVEL_STRING.format(*check) + ".lvl",
                commands = {
                    r"ar_ids\d+=(\d+)": add_item_id,
                },
                encoding = 'utf-8',
            )

            obj_id = list(self.current_id_set).pop() # TODO: make this random somehow
            output[LEVEL_STRING.format(*check) + "_bonus_id"] = obj_id

        for quest, quest_dict in KEY_QUESTS.items():
            check = quest_dict["task"]
            output[LEVEL_STRING.format(*check) + "_quest"] = quest

        return output


class FilePatcher:
    def __init__(self):
        self.file_helper = FileHelper()

    def set_root(self, directory):
        self.file_helper.set_root(directory / "data")
        self.directory = (directory / "data")
        self.update_directory = (directory / "update" / "data")

    def replace_level_object_image(self, lvl_name, obj_id, new_img = None): # TODO: also do names of objects
        self.looking_for_obj = False
        self.capture_name = False
        self.name_to_capture = None
        self.captured_name = None

        def look_for_obj_id(line_number = None):
            self.looking_for_obj = True
            if self.capture_name and (self.name_to_capture is not None):
                self.captured_name = self.name_to_capture

            self.capture_name = False
            self.name_to_capture = None
        
        def get_name(obj_name, name_extension, line_number = None):
            if self.looking_for_obj:
                self.name_to_capture = {
                    "filename": obj_name,
                    "file_ext": name_extension,
                    "line_num": line_number
                }
        
        def get_id(found_obj_id, line_number = None):
            if self.looking_for_obj and found_obj_id == obj_id:
                self.capture_name = True

        self.file_helper.process_script(
            file = lvl_name + ".lvl",
            commands = {
                re.escape("<obj/>"): look_for_obj_id,
                r"id=(\d+)": get_id,
                r"name=(\S+)\.(\S+)": get_name,
            },
            encoding = 'utf-8',
            get_line_number = True,
        )
        look_for_obj_id()

        if self.captured_name is None: return

        # TODO: add alpha jpg support
        if new_img is None:
            new_img = FILES_DIR / "test_img.png"

        obj_dir = self.directory / "objects"

        alpha_jpg = False
        if self.captured_name["file_ext"] == "tga" and any(obj_dir.rglob(f"_a_{self.captured_name["filename"]}.jpg")):
            alpha_jpg = True

        self.file_helper.replace_script_lines(
            file = lvl_name + ".lvl",
            replacements = [{
                "line_num": self.captured_name["line_num"],
                "contents": f"name={new_img.stem}.{self.captured_name["file_ext"]}",
            }],
            encoding = 'utf-8',
            new_root_dir = self.update_directory,
        )

        img = Image.open(new_img)

        old_file_ext = next(itertools.chain(
            obj_dir.rglob(f"{self.captured_name["filename"]}.*"),
            obj_dir.rglob(f"_a_{self.captured_name["filename"]}.*"),
        )).suffix
        img_file = obj_dir / "!!!!!!modded" / f"{new_img.stem}{old_file_ext}"
        img_file.parent.mkdir(parents=True, exist_ok=True)
        alpha = img.getchannel("A").tobytes()

        if alpha_jpg:
            img_file = img_file.with_name(f"_a_{img_file.name}")

        if old_file_ext == ".jpg":
            img = img.convert("RGB")

        img.save(str(img_file))

        if alpha_jpg:
            with open(img_file, "ab") as jpg:
                jpg.write(alpha)


class FileHelper:
    def set_root(self, directory):
        self.directory = directory

    def replace_script_lines(self, file, replacements, encoding = 'utf-16', new_root_dir = None):
        if new_root_dir is None: new_root_dir = self.directory

        directory_to_check = self.directory

        file_to_open = next(directory_to_check.rglob(file))
        with open(file_to_open, "r", encoding = encoding, errors = 'replace') as script:
            lines = script.readlines()

        for info_dict in replacements:
            lines[info_dict["line_num"] - 1] = f"{info_dict["contents"]}\n"

        replacement_file = file_to_open.relative_to(directory_to_check)
        (new_root_dir / replacement_file).parent.mkdir(parents=True, exist_ok=True)

        with open(new_root_dir / replacement_file, "w", encoding = encoding) as new_script:
            new_script.writelines(lines)

    def process_script(self, file, commands, encoding = 'utf-16', get_line_number = False):
        with open(next(self.directory.rglob(file)), "r", encoding = encoding, errors = 'replace') as script:
            block_comment = False
            for line_number, line in enumerate(script, start = 1):
                line = line.strip()
                if "/*" in line: block_comment = True
                if "*/" in line: block_comment = False

                if not line or line.startswith("//") or block_comment: continue

                for pattern, function in commands.items():
                    match_expression = re.search(pattern, line)
                    if match_expression:
                        args = match_expression.groups()
                        processed_args = [int(a) if a.isdigit() else a for a in args]
                        function(*processed_args, line_number) if get_line_number else function(*processed_args)
                        break