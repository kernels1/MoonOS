import os
import shutil


class MoonFS:
    def __init__(self, drive_name="MoonDrive"):
        self.root_path = os.path.abspath(os.path.dirname(__file__))
        self.drive = drive_name
        self.drive_path = self.drive if os.path.isabs(drive_name) else os.path.join(self.root_path, drive_name)
        if not os.path.exists(self.drive_path):
            os.makedirs(self.drive_path)
        self.current_dir = ""

    def get_full_path(self, filename=""):
        base = os.path.join(self.drive_path, self.current_dir)
        full_path = os.path.normpath(os.path.join(base, filename))
        return full_path

    def change_dir(self, target):
        if target == "..":
            if self.current_dir == "" or self.current_dir == ".":
                return False
            self.current_dir = os.path.dirname(self.current_dir)
            return True

        target_path = os.path.join(self.get_full_path(), target)
        if os.path.isdir(target_path):
            self.current_dir = os.path.normpath(os.path.join(self.current_dir, target))
            return True
        return False

    def list_files(self):
        path = self.get_full_path()
        return os.listdir(path)

    def read_file(self, filename):
        path = self.get_full_path(filename)
        if os.path.exists(path) and os.path.isfile(path):
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        return None

    def delete_file(self, filename):
        path = self.get_full_path(filename)
        if os.path.exists(path):
            try:
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)
                return True
            except: return "ACCESS_DENIED"
        return False

    def create_directory(self, dirname):
        path = self.get_full_path(dirname)
        try:
            os.makedirs(path, exist_ok=True)
            return True
        except: return False

    def search_files(self, query):
        results = []
        for root, dirs, files in os.walk(self.drive):
            for name in files + dirs:
                if query.lower() in name.lower():
                    rel_path = os.path.relpath(os.path.join(root, name), self.drive)
                    results.append(rel_path)
        return results