"""Items, inventory actions, and the village shop."""

from dataclasses import dataclass

from skills import SKILL_COSTS, SKILL_LIBRARY


@dataclass(frozen=True)
class Item:
    item_id: str
    name: str
    price: int
    healing: int
    description: str


ITEMS = {
    "potion": Item("potion", "Potion", 8, 25, "Restores 25 HP."),
    "greater_potion": Item(
        "greater_potion", "Greater Potion", 18, 60, "Restores 60 HP."
    ),
}


class Inventory:
    def __init__(self, player) -> None:
        self.player = player

    def show(self) -> None:
        print("\n\033[93mInventory\033[0m")
        if not self.player.inventory:
            print("  Empty")
        for item_id, quantity in self.player.inventory.items():
            item = ITEMS.get(item_id)
            label = item.name if item else item_id.replace("_", " ").title()
            print(f"  {label}: {quantity}")

    def use(self, item_id: str) -> str:
        item = ITEMS.get(item_id)
        quantity = self.player.inventory.get(item_id, 0)
        if item is None or quantity < 1:
            return "You do not have that item."
        if self.player.hp >= self.player.max_hp:
            return "Your HP is already full."
        healed = min(item.healing, self.player.max_hp - self.player.hp)
        self.player.hp += healed
        self.player.inventory[item_id] -= 1
        if self.player.inventory[item_id] == 0:
            del self.player.inventory[item_id]
        return f"You used {item.name} and restored {healed} HP."


class Shop:
    def open(self, player) -> None:
        while True:
            print(
                "\n\033[93mTRADER'S SHOP\033[0m"
                f"\nGold: {player.gold}"
                "\n1) Potion - 8 gold"
                "\n2) Greater Potion - 18 gold"
            )
            for index, (skill_id, price) in enumerate(SKILL_COSTS.items(), start=3):
                skill = SKILL_LIBRARY[skill_id]
                state = " (learned)" if skill_id in player.skills else ""
                print(f"{index}) Learn {skill.name} - {price} gold{state}")
            print("0) Leave")
            choice = input("Choose: ").strip()
            if choice == "0":
                return
            try:
                number = int(choice)
            except ValueError:
                print("Enter one of the listed numbers.")
                continue
            if number == 1 or number == 2:
                item_id = "potion" if number == 1 else "greater_potion"
                item = ITEMS[item_id]
                if player.gold < item.price:
                    print("Not enough gold.")
                    continue
                player.gold -= item.price
                player.inventory[item_id] = player.inventory.get(item_id, 0) + 1
                print(f"Bought {item.name}.")
                continue
            skill_index = number - 3
            skill_ids = list(SKILL_COSTS)
            if 0 <= skill_index < len(skill_ids):
                skill_id = skill_ids[skill_index]
                if skill_id in player.skills:
                    print("You already know that skill.")
                elif player.gold < SKILL_COSTS[skill_id]:
                    print("Not enough gold.")
                else:
                    player.gold -= SKILL_COSTS[skill_id]
                    player.skills.append(skill_id)
                    print(f"Learned {SKILL_LIBRARY[skill_id].name}!")
            else:
                print("Enter one of the listed numbers.")
