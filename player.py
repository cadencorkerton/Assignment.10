"""Player character state, progression, and save conversion."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Player:
    username: str
    level: int = 1
    xp: int = 0
    gold: int = 25
    hp: int = 60
    max_hp: int = 60
    location: str = "Village"
    x: int = 2
    y: int = 2
    inventory: dict[str, int] = field(default_factory=lambda: {"potion": 2})
    skills: list[str] = field(default_factory=lambda: ["power_strike"])
    cooldowns: dict[str, int] = field(default_factory=dict)
    quests: dict[str, Any] = field(default_factory=dict)

    def add_xp(self, amount: int) -> list[str]:
        self.xp += max(0, amount)
        messages = []
        while self.xp >= self.level * 100:
            self.xp -= self.level * 100
            self.level += 1
            self.max_hp += 12
            self.hp = self.max_hp
            messages.append(f"Level up! You are now level {self.level}; HP restored.")
        return messages

    def to_dict(self) -> dict[str, Any]:
        return {
            "level": self.level,
            "xp": self.xp,
            "gold": self.gold,
            "hp": self.hp,
            "max_hp": self.max_hp,
            "location": self.location,
            "x": self.x,
            "y": self.y,
            "inventory": self.inventory,
            "skills": self.skills,
            "cooldowns": self.cooldowns,
            "quests": self.quests,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Player":
        player = cls(username=str(data["username"]))
        for field_name in ("level", "xp", "gold", "hp", "max_hp", "x", "y"):
            value = data.get(field_name, getattr(player, field_name))
            if isinstance(value, int) and not isinstance(value, bool):
                setattr(player, field_name, max(0, value))
        if data.get("location") in {"Village", "Ruins"}:
            player.location = data["location"]
        inventory = data.get("inventory")
        if isinstance(inventory, dict):
            player.inventory = {
                key: value
                for key, value in inventory.items()
                if isinstance(key, str)
                and isinstance(value, int)
                and not isinstance(value, bool)
                and value > 0
            }
        cooldowns = data.get("cooldowns")
        if isinstance(cooldowns, dict):
            player.cooldowns = {
                key: value
                for key, value in cooldowns.items()
                if isinstance(key, str)
                and isinstance(value, int)
                and not isinstance(value, bool)
                and value > 0
            }
        quests = data.get("quests")
        if isinstance(quests, dict):
            player.quests = quests
        skills = data.get("skills")
        if isinstance(skills, list):
            player.skills = [skill for skill in skills if isinstance(skill, str)]
        player.level = max(1, player.level)
        player.max_hp = max(1, player.max_hp)
        player.hp = min(player.hp, player.max_hp)
        return player
