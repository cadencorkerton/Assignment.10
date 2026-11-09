"""Monster base class and five distinct enemy types."""

import random


class Monster:
    def __init__(
        self,
        name: str,
        hp: int,
        attack: int,
        xp_reward: int,
        gold_range: tuple[int, int],
        drop_item: str | None = None,
    ) -> None:
        self.name = name
        self.hp = hp
        self.max_hp = hp
        self.attack = attack
        self.xp_reward = xp_reward
        self.gold_range = gold_range
        self.drop_item = drop_item

    def strike(self) -> int:
        return random.randint(max(1, self.attack - 3), self.attack + 3)

    def reward(self) -> tuple[int, str | None]:
        gold = random.randint(*self.gold_range)
        item = self.drop_item if self.drop_item and random.random() < 0.35 else None
        return gold, item


class Goblin(Monster):
    def __init__(self) -> None:
        super().__init__("Goblin", 24, 7, 25, (4, 9), "potion")


class Wolf(Monster):
    def __init__(self) -> None:
        super().__init__("Wolf", 32, 9, 32, (5, 11), "potion")


class Skeleton(Monster):
    def __init__(self) -> None:
        super().__init__("Skeleton", 38, 10, 40, (7, 13), "greater_potion")


class Troll(Monster):
    def __init__(self) -> None:
        super().__init__("Troll", 58, 13, 55, (10, 18), "greater_potion")


class FinalBoss(Monster):
    def __init__(self) -> None:
        super().__init__("The Ashen King", 125, 16, 200, (50, 50), None)
