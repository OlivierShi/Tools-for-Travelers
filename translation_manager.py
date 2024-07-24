from sqlite import SQLiteStorage
from config import BaseConfig

class TranslationManager:
    def __init__(self, storage: SQLiteStorage):
        self.storage = storage

        storage.create_table("translations", "id TEXT PRIMARY KEY, datetime TEXT, Chinese TEXT, Russian TEXT, English TEXT")

    def save_translation(self, id, datetime, Chinese="", Russian="", English=""):
        self.storage.upsert("translations", {"id": id, "datetime": datetime, "Chinese": Chinese, "Russian": Russian, "English": English})

    def get_translation_history(self):
        rows = self.storage.fetchall("translations")

        history = []

        for row in rows:
            history.append({
                "id": row[0],
                "datetime": row[1],
                "Chinese": row[2],
                "Russian": row[3],
                "English": row[4]
            })

        return history




