import json
import os


class CatalogManager:
    def __init__(self, json_path):
        self.json_path = json_path

    def load(self):
        if not os.path.exists(self.json_path):
            return {"modo": "Catálogo general", "apps": []}

        with open(self.json_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def save(self, data):
        with open(self.json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def get_apps(self):
        return self.load().get("apps", [])

    def add_app(self, app_data):
        data = self.load()
        data.setdefault("apps", []).append(app_data)
        self.save(data)

    def update_app_by_name(self, original_name, updated_app):
        data = self.load()
        apps = data.setdefault("apps", [])

        for i, app in enumerate(apps):
            if app.get("nombre") == original_name:
                apps[i] = updated_app
                self.save(data)
                return True

        return False
    def delete_app_by_name(self, app_name):
        data = self.load()
        apps = data.setdefault("apps", [])

        original_len = len(apps)
        apps = [app for app in apps if app.get("nombre") != app_name]
        data["apps"] = apps

        if len(apps) == original_len:
            return False

        self.save(data)
        return True