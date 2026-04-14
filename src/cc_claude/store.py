import json
import os
import shutil
from datetime import datetime, timezone

from platformdirs import user_data_dir


DATA_DIR = user_data_dir("cc-claude", appauthor=False)
DATA_FILE = os.path.join(DATA_DIR, "projects.json")


class ProjectStore:
    def __init__(self):
        self.data_dir = DATA_DIR
        self.data_file = DATA_FILE

    def _load(self):
        if not os.path.exists(self.data_file):
            return {"projects": []}
        try:
            with open(self.data_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            if "projects" not in data:
                return {"projects": []}
            return data
        except (json.JSONDecodeError, OSError):
            return {"projects": []}

    def _save(self, data):
        os.makedirs(self.data_dir, exist_ok=True)
        with open(self.data_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def list_projects(self):
        """Return projects sorted by last_opened_at descending (most recent first)."""
        data = self._load()
        projects = data["projects"]
        projects.sort(key=lambda p: p.get("last_opened_at", ""), reverse=True)
        return projects

    def add_project(self, path):
        """Add a project. Idempotent: if path already tracked, update last_opened_at."""
        path = os.path.realpath(path)
        name = os.path.basename(path)
        data = self._load()
        now = datetime.now(timezone.utc).isoformat()

        # Check if this path is already tracked
        for proj in data["projects"]:
            if os.path.realpath(proj["path"]) == path:
                proj["last_opened_at"] = now
                self._save(data)
                return proj

        # Check for duplicate name
        for proj in data["projects"]:
            if proj["name"].lower() == name.lower():
                raise ValueError(
                    f"A project named '{proj['name']}' already exists "
                    f"at {proj['path']}. Remove it first with: cc rm {proj['name']}"
                )

        project = {
            "name": name,
            "path": path,
            "added_at": now,
            "last_opened_at": now,
        }
        data["projects"].append(project)
        self._save(data)
        return project

    def get_project(self, name):
        """Lookup a project by name (case-insensitive)."""
        data = self._load()
        for proj in data["projects"]:
            if proj["name"].lower() == name.lower():
                return proj
        return None

    def touch_project(self, name):
        """Update last_opened_at for a project."""
        data = self._load()
        now = datetime.now(timezone.utc).isoformat()
        for proj in data["projects"]:
            if proj["name"].lower() == name.lower():
                proj["last_opened_at"] = now
                self._save(data)
                return proj
        return None

    def remove_project(self, name):
        """Remove a project by name. Returns True if found and removed."""
        data = self._load()
        original_len = len(data["projects"])
        data["projects"] = [
            p for p in data["projects"] if p["name"].lower() != name.lower()
        ]
        if len(data["projects"]) < original_len:
            self._save(data)
            return True
        return False

    def purge(self):
        """Delete all stored data."""
        if os.path.exists(self.data_dir):
            shutil.rmtree(self.data_dir)
