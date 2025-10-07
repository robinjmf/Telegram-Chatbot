import json
import os
from typing import Any, Dict, Optional
from threading import RLock


class JsonMemory:
    def __init__(self, path: str) -> None:
        self.path = path
        self._lock = RLock()
        os.makedirs(os.path.dirname(path), exist_ok=True)
        if not os.path.exists(path):
            with open(path, "w", encoding="utf-8") as f:
                json.dump({}, f)

    def _read_all(self) -> Dict[str, Any]:
        with self._lock:
            if not os.path.exists(self.path):
                return {}
            with open(self.path, "r", encoding="utf-8") as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    return {}

    def _write_all(self, data: Dict[str, Any]) -> None:
        with self._lock:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

    def get_profile(self, user_id: int) -> Optional[Dict[str, Any]]:
        data = self._read_all()
        return data.get(str(user_id), {}).get("profile")

    def set_profile(self, user_id: int, profile: Dict[str, Any]) -> None:
        data = self._read_all()
        user_key = str(user_id)
        user_bucket = data.get(user_key, {})
        user_bucket["profile"] = profile
        data[user_key] = user_bucket
        self._write_all(data)

    def set_last_goals(self, user_id: int, goals_text: str) -> None:
        data = self._read_all()
        user_key = str(user_id)
        user_bucket = data.get(user_key, {})
        user_bucket["last_goals"] = goals_text
        data[user_key] = user_bucket
        self._write_all(data)

    def get_last_goals(self, user_id: int) -> Optional[str]:
        data = self._read_all()
        return data.get(str(user_id), {}).get("last_goals")

    def reset(self, user_id: int) -> None:
        data = self._read_all()
        user_key = str(user_id)
        if user_key in data:
            del data[user_key]
        self._write_all(data)
