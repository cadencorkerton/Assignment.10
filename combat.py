"""Turn-based combat, skill cooldowns, and victory rewards."""

from items import Inventory
from monsters import Monster
from player import Player
from skills import SKILL_LIBRARY


def fight(player: Player, monster: Monster) -> bool:
    print(f"\n\033[91mA {monster.name} attacks!\033[0m")
    while player.hp > 0 and monster.hp > 0:
        print(f"\nHP {player.hp}/{player.max_hp} | {monster.name} HP {monster.hp}")
        available_skills = [
            skill_id
            for skill_id in player.skills
            if skill_id in SKILL_LIBRARY
        ]
        print("A) Attack  P) Potion  R) Run")
        for index, skill_id in enumerate(available_skills, start=1):
            skill = SKILL_LIBRARY[skill_id]
            remaining = player.cooldowns.get(skill_id, 0)
            state = f" (cooldown {remaining})" if remaining else ""
            print(f"{index}) {skill.name}{state}")
        action = input("Combat action: ").strip().casefold()

        if action == "r":
            print("You escaped.")
            return False
        if action == "p":
            potion_ids = [
                item_id
                for item_id, quantity in player.inventory.items()
                if item_id in {"potion", "greater_potion"} and quantity > 0
            ]
            if not potion_ids:
                print("You have no healing potions.")
                continue
            print("Potions: " + ", ".join(potion_ids))
            item_id = input("Type an item name, or press Enter to cancel: ").strip()
            if not item_id:
                continue
            message = Inventory(player).use(item_id)
            print(message)
            if message.startswith("You used"):
                _monster_turn(player, monster)
            continue
        if action == "a":
            damage = 8 + player.level * 3
            monster.hp -= damage
            print(f"You hit for {damage} damage.")
        else:
            try:
                skill_index = int(action) - 1
            except ValueError:
                print("Choose A, P, R, or one of the skill numbers.")
                continue
            if not 0 <= skill_index < len(available_skills):
                print("That skill number is not available.")
                continue
            skill_id = available_skills[skill_index]
            if player.cooldowns.get(skill_id, 0) > 0:
                print("That skill is still cooling down.")
                continue
            skill = SKILL_LIBRARY[skill_id]
            damage, _, message = skill.use(player, monster)
            if damage == 0 and skill_id == "healing_light" and player.hp >= player.max_hp:
                print(message)
                continue
            monster.hp -= damage
            player.cooldowns[skill_id] = skill.cooldown
            print(message)

        if monster.hp <= 0:
            break
        _monster_turn(player, monster)
        for skill_id in player.cooldowns:
            player.cooldowns[skill_id] = max(0, player.cooldowns[skill_id] - 1)

    if player.hp <= 0:
        print("\033[91mYou were defeated. Return to the village to recover.\033[0m")
        return False

    gold, item_id = monster.reward()
    player.gold += gold
    print(f"\033[93m{monster.name} defeated! +{gold} gold, +{monster.xp_reward} XP.\033[0m")
    if item_id:
        player.inventory[item_id] = player.inventory.get(item_id, 0) + 1
        print(f"The monster dropped {item_id.replace('_', ' ').title()}!")
    for message in player.add_xp(monster.xp_reward):
        print(f"\033[96m{message}\033[0m")
    return True


def _monster_turn(player: Player, monster: Monster) -> None:
    damage = monster.strike()
    player.hp = max(0, player.hp - damage)
    print(f"{monster.name} hits you for {damage} damage.")
