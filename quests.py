"""Multi-step main quest and two optional side quests."""


class QuestBook:
    def __init__(self, player) -> None:
        self.player = player
        self.data = player.quests
        self.data.setdefault("main_step", 0)
        self.data.setdefault("main_kills", 0)
        self.data.setdefault("side_started", [])
        self.data.setdefault("side_done", [])
        self.data.setdefault("defeated_spawns", [])
        step = self.data["main_step"]
        self.data["main_step"] = (
            min(max(step, 0), 4)
            if isinstance(step, int) and not isinstance(step, bool)
            else 0
        )
        kills = self.data["main_kills"]
        self.data["main_kills"] = (
            max(kills, 0)
            if isinstance(kills, int) and not isinstance(kills, bool)
            else 0
        )
        for key in ("side_started", "side_done", "defeated_spawns"):
            if not isinstance(self.data[key], list):
                self.data[key] = []
            else:
                self.data[key] = [value for value in self.data[key] if isinstance(value, str)]

    @property
    def defeated_spawns(self) -> list[str]:
        value = self.data.get("defeated_spawns", [])
        return value if isinstance(value, list) else []

    def main_objective(self) -> str:
        step = self.data["main_step"]
        objectives = [
            "Speak with Elder Rowan in the village.",
            f"Defeat 3 monsters ({self.data['main_kills']}/3).",
            "Find Sage Elowen in the ruins.",
            "Defeat the Ashen King in the ruins.",
            "Complete! The Ashen King is defeated.",
        ]
        return objectives[min(step, 4)]

    def speak_to(self, npc_id: str) -> str | None:
        step = self.data["main_step"]
        if npc_id == "elder" and step == 0:
            self.data["main_step"] = 1
            return "Main quest started: defeat three monsters, then seek the sage."
        if npc_id == "sage" and step == 2:
            self.data["main_step"] = 3
            self.player.inventory["royal_sigil"] = 1
            return "Main quest: the sigil is yours. Find the Ashen King!"
        return None

    def start_side(self, quest_id: str) -> str:
        started = self.data["side_started"]
        done = self.data["side_done"]
        if quest_id in done:
            return "You have already completed this request."
        if quest_id in started:
            return "You have already accepted this request."
        started.append(quest_id)
        if quest_id == "potion_request":
            self.data["potion_baseline"] = self.player.inventory.get("potion", 0)
        return "Side quest accepted!"

    def record_kill(self, monster_id: str, spawn_id: str) -> list[str]:
        self.data["defeated_spawns"].append(spawn_id)
        messages = []
        if self.data["main_step"] == 1:
            self.data["main_kills"] += 1
            if self.data["main_kills"] >= 3:
                self.data["main_step"] = 2
                messages.append("Main quest: three monsters defeated. Find the sage in the ruins.")
        if "wolf_hunt" in self.data["side_started"] and "wolf_hunt" not in self.data["side_done"]:
            if monster_id == "wolf":
                count = self.data.get("wolf_kills", 0) + 1
                self.data["wolf_kills"] = count
                if count >= 2:
                    self._complete_side("wolf_hunt", 25, 50)
                    messages.append("Hunter Bram's quest complete: +25 gold and +50 XP.")
        return messages

    def check_potion_quest(self) -> list[str]:
        if (
            "potion_request" in self.data["side_started"]
            and "potion_request" not in self.data["side_done"]
            and self.player.inventory.get("potion", 0)
            >= self.data.get("potion_baseline", 0) + 2
        ):
            self._complete_side("potion_request", 20, 35)
            return ["Sister Fern's quest complete: +20 gold and +35 XP."]
        return []

    def _complete_side(self, quest_id: str, gold: int, xp: int) -> None:
        self.data["side_done"].append(quest_id)
        self.player.gold += gold
        self.player.add_xp(xp)

    def finish_boss(self) -> None:
        self.data["main_step"] = 4

    def show(self) -> None:
        print("\n\033[96mQUESTS\033[0m")
        print(f"Main: {self.main_objective()}")
        labels = {
            "wolf_hunt": f"Hunt: defeat two wolves ({self.data.get('wolf_kills', 0)}/2).",
            "potion_request": "Supply: bring Sister Fern two potions.",
        }
        for quest_id, label in labels.items():
            if quest_id in self.data["side_done"]:
                print(f"Side: {label} Complete")
            elif quest_id in self.data["side_started"]:
                print(f"Side: {label}")
