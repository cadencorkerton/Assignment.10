"""Learnable skills use inheritance for their different effects."""


class Skill:
    def __init__(self, skill_id: str, name: str, cooldown: int) -> None:
        self.skill_id = skill_id
        self.name = name
        self.cooldown = cooldown

    def use(self, player, monster) -> tuple[int, int, str]:
        raise NotImplementedError("Each skill must define its effect.")


class PowerStrike(Skill):
    def __init__(self) -> None:
        super().__init__("power_strike", "Power Strike", 1)

    def use(self, player, monster) -> tuple[int, int, str]:
        damage = 18 + player.level * 4
        return damage, 0, f"You strike with force for {damage} damage."


class Fireball(Skill):
    def __init__(self) -> None:
        super().__init__("fireball", "Fireball", 2)

    def use(self, player, monster) -> tuple[int, int, str]:
        damage = 25 + player.level * 5
        return damage, 0, f"A fireball scorches the enemy for {damage} damage."


class HealingLight(Skill):
    def __init__(self) -> None:
        super().__init__("healing_light", "Healing Light", 3)

    def use(self, player, monster) -> tuple[int, int, str]:
        if player.hp >= player.max_hp:
            return 0, 0, "Your HP is already full."
        healed = min(28 + player.level * 5, player.max_hp - player.hp)
        player.hp += healed
        return 0, healed, f"Healing Light restores {healed} HP."


SKILL_LIBRARY = {
    skill.skill_id: skill
    for skill in (PowerStrike(), Fireball(), HealingLight())
}
SKILL_COSTS = {"fireball": 12, "healing_light": 15}
