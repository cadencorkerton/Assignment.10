"""Entry point for The Shattered Crown."""

from auth import authenticate
from combat import fight
from database import GameDatabase
from items import Inventory, Shop
from monsters import FinalBoss, Goblin, Skeleton, Troll, Wolf
from player import Player
from quests import QuestBook
from world import ENCOUNTERS, GameWorld, read_key


MONSTERS = {
    "goblin": Goblin,
    "wolf": Wolf,
    "skeleton": Skeleton,
    "troll": Troll,
}


class Game:
    def __init__(self, database: GameDatabase, player: Player) -> None:
        self.database = database
        self.player = player
        self.world = GameWorld()
        self.world.ensure_valid_position(player)
        self.quests = QuestBook(player)
        self.shop = Shop()
        self.first_visit = not player.quests.get("intro_seen", False)

    def run(self) -> None:
        if self.first_visit:
            self._story_intro()
            self.player.quests["intro_seen"] = True
        while self.player.quests.get("main_step", 0) < 4:
            self.world.display(
                self.player,
                self.quests.defeated_spawns,
                self.player.quests.get("main_step") == 4,
            )
            key = read_key()
            self.world.clear_output()
            if key in {"w", "a", "s", "d"}:
                if self.world.move(self.player, key):
                    self._check_encounter()
            elif key == "e":
                self._interact()
            elif key == "i":
                Inventory(self.player).show()
                for message in self.quests.check_potion_quest():
                    print(message)
            elif key == "c":
                self._show_character()
            elif key == "j":
                self.quests.show()
            elif key in {"q", "\x03"}:
                self._save()
                print("Progress saved. See you soon!")
                return
            self._save()
            if self.player.hp <= 0:
                self.player.location = "Village"
                self.player.x, self.player.y = 2, 2
                self.player.hp = max(1, self.player.max_hp // 2)
                print("The healer brings you back to the village at half HP.")
                self._save()

        if self.player.quests.get("main_step") == 4:
            print("\n\033[93mTHE ASHEN KING FALLS!\033[0m")
            print("The crown breaks, the ruins grow quiet, and the village is free. You win!")
            self._show_character()
            self._save()

    @staticmethod
    def _story_intro() -> None:
        print(
            "\nA century ago, the Ashen King was sealed beneath the old ruins. "
            "Tonight, the seal shattered. Dark creatures now stalk the roads, "
            "and the king is gathering strength.\n"
            "Elder Rowan asks you to help the village. Explore, meet its people, "
            "learn skills, and follow the trail to the ruins. Defeat the Ashen King "
            "to restore peace.\n"
        )

    def _check_encounter(self) -> None:
        position = (self.player.x, self.player.y)
        self._fight_monster_at(position)
        if self.world.at_boss(self.player):
            if self.player.quests.get("main_step") < 3:
                print(
                    "A royal sigil is needed to challenge the Ashen King. "
                    "Continue your quest."
                )
            elif self.player.quests.get("main_step") == 3:
                if fight(self.player, FinalBoss()):
                    self.quests.finish_boss()

    def _fight_monster_at(self, position: tuple[int, int]) -> None:
        monster_id = ENCOUNTERS[self.player.location].get(position)
        spawn_id = f"{self.player.location}:{position[0]},{position[1]}"
        if monster_id and spawn_id not in self.quests.defeated_spawns:
            print(f"You engage the {monster_id.title()}!")
            won = fight(self.player, MONSTERS[monster_id]())
            if won:
                for message in self.quests.record_kill(monster_id, spawn_id):
                    print(message)

    def _interact(self) -> None:
        nearby_npcs = self.world.nearby_npcs(self.player)
        nearby_monsters = [
            (monster_id, position)
            for position, monster_id in ENCOUNTERS[self.player.location].items()
            if f"{self.player.location}:{position[0]},{position[1]}"
            not in self.quests.defeated_spawns
            and abs(position[0] - self.player.x) + abs(position[1] - self.player.y) <= 1
        ]
        targets = [
            ("person", npc_id, npc)
            for npc_id, npc in nearby_npcs
        ] + [
            ("monster", monster_id, position)
            for monster_id, position in nearby_monsters
        ]
        if not targets:
            if self.world.at_boss(self.player):
                self._check_encounter()
            else:
                print("No person or monster is close enough to interact with.")
            return
        if len(targets) == 1:
            self._interact_with_target(*targets[0])
            return
        for index, (kind, target_id, target) in enumerate(targets, start=1):
            label = target["name"] if kind == "person" else target_id.title()
            action = "Talk to" if kind == "person" else "Fight"
            print(f"{index}) {action} {label}")
        try:
            selected = int(input("Choose a target: ")) - 1
        except ValueError:
            print("Enter a listed number.")
            return
        if 0 <= selected < len(targets):
            self._interact_with_target(*targets[selected])
        else:
            print("That target is not listed.")

    def _interact_with_target(self, kind: str, target_id: str, target) -> None:
        if kind == "person":
            self._talk(target_id, target)
        else:
            self._fight_monster_at(target)

    def _talk(self, npc_id: str, npc: dict) -> None:
        print(f"\n\033[96m{npc['name']}:\033[0m {npc['dialogue']}")
        if npc_id == "trader":
            self.shop.open(self.player)
            for message in self.quests.check_potion_quest():
                print(message)
            return
        if npc_id == "healer":
            print(self.quests.start_side("potion_request"))
            if self.player.hp < self.player.max_hp:
                answer = input("Pay 5 gold for a full heal? (y/n): ").strip().casefold()
                if answer == "y" and self.player.gold >= 5:
                    self.player.gold -= 5
                    self.player.hp = self.player.max_hp
                    print("Your wounds are healed.")
                elif answer == "y":
                    print("You need 5 gold.")
        elif npc_id == "hunter":
            print(self.quests.start_side("wolf_hunt"))
        else:
            message = self.quests.speak_to(npc_id)
            if message:
                print(message)
        for message in self.quests.check_potion_quest():
            print(message)

    def _show_character(self) -> None:
        skills = ", ".join(
            skill_id.replace("_", " ").title() for skill_id in self.player.skills
        )
        print(
            f"\n\033[96m{self.player.username} — Level {self.player.level}\033[0m"
            f"\nHP: {self.player.hp}/{self.player.max_hp}"
            f"\nXP: {self.player.xp}/{self.player.level * 100}"
            f"\nGold: {self.player.gold}"
            f"\nLocation: {self.player.location} ({self.player.x}, {self.player.y})"
            f"\nSkills: {skills or 'None'}"
        )
        Inventory(self.player).show()
        self.quests.show()

    def _save(self) -> None:
        self.database.save_game(self.player.username, self.player.to_dict())


def main() -> None:
    print("\033[96m" + "=" * 58)
    print("                 THE SHATTERED CROWN")
    print("=" * 58 + "\033[0m")
    database = GameDatabase()
    try:
        username = authenticate(database)
        if username is None:
            print("See you next time.")
            return
        saved_game = database.load_game(username)
        player = Player.from_dict(saved_game) if saved_game else Player(username=username)
        Game(database, player).run()
    except (KeyboardInterrupt, EOFError):
        print("\nGame closed. Your last saved progress is safe.")
    finally:
        database.close()


if __name__ == "__main__":
    main()
