"""TinyDB account and game-progress storage."""

from pathlib import Path
from typing import Any

from tinydb import Query, TinyDB


class GameDatabase:
    def __init__(self, path: Path | None = None) -> None:
        self._db = TinyDB(path or Path(__file__).with_name("saves.json"), indent=2)
        self._accounts = self._db.table("accounts")
        self._games = self._db.table("games")

    def get_account(self, username: str) -> dict[str, Any] | None:
        record = self._accounts.get(Query().username == username.casefold())
        return dict(record) if record else None

    def create_account(self, username: str, salt: str, password_hash: str) -> bool:
        normalized = username.casefold()
        if self._accounts.contains(Query().username == normalized):
            return False
        self._accounts.insert(
            {"username": normalized, "salt": salt, "password_hash": password_hash}
        )
        return True

    def load_game(self, username: str) -> dict[str, Any] | None:
        record = self._games.get(Query().username == username.casefold())
        return dict(record) if record else None

    def save_game(self, username: str, data: dict[str, Any]) -> None:
        self._games.upsert(
            {"username": username.casefold(), **data},
            Query().username == username.casefold(),
        )

    def close(self) -> None:
        self._db.close()
