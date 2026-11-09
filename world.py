"""Two hand-built maps, colored rendering, NPCs, and instant key input."""

import os
import subprocess
import sys


def _carve(width: int, height: int, rooms: list[tuple[int, int, int, int]]) -> list[list[str]]:
    grid = [["#"] * width for _ in range(height)]
    for left, top, right, bottom in rooms:
        for y in range(top, bottom + 1):
            for x in range(left, right + 1):
                grid[y][x] = "."
    return grid


VILLAGE = _carve(
    20,
    12,
    [
        (1, 1, 5, 3), (5, 2, 12, 2), (10, 1, 17, 3),
        (7, 3, 7, 8), (1, 6, 5, 10), (5, 6, 15, 6),
        (13, 5, 18, 10), (8, 8, 13, 8), (11, 3, 11, 8),
        (1, 9, 3, 10), (16, 8, 18, 10),
    ],
)
RUINS = _carve(
    26,
    16,
    [
        (1, 1, 5, 5), (5, 3, 13, 3), (11, 1, 17, 6),
        (3, 6, 17, 6), (3, 5, 3, 11), (1, 10, 8, 14),
        (8, 11, 21, 11), (17, 8, 23, 14), (20, 5, 20, 9),
        (17, 6, 20, 6), (21, 11, 22, 13),
    ],
)
VILLAGE[9][18] = ">"
RUINS[13][2] = "<"

NPCS = {
    "elder": {
        "name": "Elder Rowan", "map": "Village", "x": 2, "y": 2, "glyph": "E",
        "dialogue": "The Ashen King has awakened. The village needs a brave hero.",
    },
    "trader": {
        "name": "Mira the Trader", "map": "Village", "x": 15, "y": 2, "glyph": "T",
        "dialogue": "Good gear keeps you alive. Browse my wares whenever you like.",
    },
    "healer": {
        "name": "Sister Fern", "map": "Village", "x": 2, "y": 9, "glyph": "F",
        "dialogue": "The wounded need supplies. Bring me two potions and I will reward you.",
    },
    "hunter": {
        "name": "Hunter Bram", "map": "Village", "x": 16, "y": 8, "glyph": "H",
        "dialogue": "Wolves stalk the old road. Defeat two and I will share my bounty.",
    },
    "sage": {
        "name": "Sage Elowen", "map": "Ruins", "x": 3, "y": 2, "glyph": "S",
        "dialogue": "The king's crown binds him to the ruins. Take this sigil to break it.",
    },
}

ENCOUNTERS = {
    "Village": {(4, 2): "goblin", (3, 7): "wolf", (14, 8): "skeleton"},
    "Ruins": {
        (8, 3): "goblin",
        (16, 6): "troll",
        (19, 10): "skeleton",
        (6, 11): "wolf",
    },
}
MONSTER_GLYPHS = {
    "goblin": "G",
    "wolf": "W",
    "skeleton": "K",
    "troll": "T",
}
SPAWN = {"village": (2, 2), "ruins": (2, 13)}
BOSS_POSITION = (22, 13)

COLORS = {
    "#": "\033[90m", ".": "\033[37m", ">": "\033[96m", "<": "\033[96m",
    "B": "\033[91m", "G": "\033[91m", "W": "\033[93m",
    "K": "\033[97m", "T": "\033[95m", "@": "\033[92m",
    "E": "\033[96m", "T": "\033[93m", "F": "\033[95m",
    "H": "\033[92m", "S": "\033[96m",
}
COMMANDS = "W/A/S/D move | E talk | I items | C stats | J quests | Q save & quit"


class GameWorld:
    def __init__(self) -> None:
        self._rendered_location: str | None = None
        self._rendered_position: tuple[int, int] | None = None
        self._rendered_defeated: set[str] = set()
        self._rendered_boss_defeated = False

    def ensure_valid_position(self, player) -> None:
        grid = VILLAGE if player.location == "Village" else RUINS
        if (
            not 0 <= player.y < len(grid)
            or not 0 <= player.x < len(grid[player.y])
            or grid[player.y][player.x] == "#"
        ):
            player.location = "Village"
            player.x, player.y = SPAWN["village"]

    def display(self, player, defeated_spawns: list[str], boss_defeated: bool) -> None:
        defeated = set(defeated_spawns)
        grid = VILLAGE if player.location == "Village" else RUINS
        if self._rendered_location != player.location:
            self._draw_map(player, defeated, boss_defeated, grid)
        else:
            old_x, old_y = self._rendered_position or (player.x, player.y)
            if (old_x, old_y) != (player.x, player.y):
                self._write_tile(
                    old_x,
                    old_y,
                    self._tile_at(player.location, old_x, old_y, defeated, boss_defeated),
                )
            for marker in self._rendered_defeated ^ defeated:
                marker_location, coordinates = marker.split(":")
                if marker_location != player.location:
                    continue
                x, y = (int(value) for value in coordinates.split(","))
                if (x, y) != (player.x, player.y):
                    self._write_tile(
                        x,
                        y,
                        self._tile_at(player.location, x, y, defeated, boss_defeated),
                    )
            if self._rendered_boss_defeated != boss_defeated:
                x, y = BOSS_POSITION
                if player.location == "Ruins" and (x, y) != (player.x, player.y):
                    self._write_tile(
                        x,
                        y,
                        self._tile_at(player.location, x, y, defeated, boss_defeated),
                    )
            self._write_tile(player.x, player.y, "@")
            self._write_status(player, len(grid))
            self._write_commands(len(grid))
            print(f"\033[{len(grid) + 5};1H", end="", flush=True)

        self._rendered_location = player.location
        self._rendered_position = (player.x, player.y)
        self._rendered_defeated = defeated
        self._rendered_boss_defeated = boss_defeated

    def _draw_map(
        self, player, defeated: set[str], boss_defeated: bool, grid: list[list[str]]
    ) -> None:
        if sys.stdout.isatty():
            try:
                command = ["cmd", "/c", "cls"] if os.name == "nt" else ["clear"]
                subprocess.run(command, check=True)
            except (OSError, subprocess.CalledProcessError):
                print("\033[2J\033[H", end="")
        else:
            print("\033[2J\033[H", end="")

        print(f"\033[96m{player.location}\033[0m")
        for y in range(len(grid)):
            print(
                "".join(
                    f"{COLORS.get(tile, '')}{tile}\033[0m"
                    for tile in self._map_row(
                        player.location, y, player, defeated, boss_defeated
                    )
                )
            )
        print("@ You | G Goblin W Wolf K Skeleton T Troll | NPCs: E/T/F/H/S | B Boss")
        self._write_status(player, len(grid))
        self._write_commands(len(grid))
        print(f"\033[{len(grid) + 5}r", end="")
        print(f"\033[{len(grid) + 5};1H", end="", flush=True)

    def _map_row(
        self, location: str, y: int, player, defeated: set[str], boss_defeated: bool
    ) -> list[str]:
        grid = VILLAGE if location == "Village" else RUINS
        row = [self._tile_at(location, x, y, defeated, boss_defeated) for x in range(len(grid[y]))]
        if y == player.y:
            row[player.x] = "@"
        return row

    @staticmethod
    def _tile_at(
        location: str, x: int, y: int, defeated: set[str], boss_defeated: bool
    ) -> str:
        grid = VILLAGE if location == "Village" else RUINS
        tile = grid[y][x]
        if location == "Ruins" and (x, y) == BOSS_POSITION and not boss_defeated:
            tile = "B"
        for npc in NPCS.values():
            if npc["map"] == location and (npc["x"], npc["y"]) == (x, y):
                tile = npc["glyph"]
        marker = f"{location}:{x},{y}"
        monster_id = ENCOUNTERS[location].get((x, y))
        if monster_id and marker not in defeated:
            tile = MONSTER_GLYPHS[monster_id]
        return tile

    @staticmethod
    def _write_tile(x: int, y: int, tile: str) -> None:
        row = y + 2
        column = x + 1
        print(
            f"\033[{row};{column}H{COLORS.get(tile, '')}{tile}\033[0m",
            end="",
        )

    @staticmethod
    def _write_status(player, map_height: int) -> None:
        row = map_height + 3
        print(
            f"\033[{row};1H\033[2K"
            f"HP {player.hp}/{player.max_hp} | Lv {player.level} | "
            f"XP {player.xp} | Gold {player.gold}",
            end="",
            flush=True,
        )

    @staticmethod
    def _write_commands(map_height: int) -> None:
        row = map_height + 4
        print(
            f"\033[{row};1H\033[2K{COMMANDS}",
            end="",
            flush=True,
        )

    def clear_output(self) -> None:
        grid = VILLAGE if self._rendered_location == "Village" else RUINS
        print(f"\033[{len(grid) + 5};1H\033[J", end="", flush=True)

    def move(self, player, key: str) -> bool:
        delta = {"w": (0, -1), "s": (0, 1), "a": (-1, 0), "d": (1, 0)}
        if key not in delta:
            return False
        dx, dy = delta[key]
        nx, ny = player.x + dx, player.y + dy
        grid = VILLAGE if player.location == "Village" else RUINS
        if not (0 <= ny < len(grid) and 0 <= nx < len(grid[ny])):
            return False
        if grid[ny][nx] == "#":
            return False
        player.x, player.y = nx, ny
        if player.location == "Village" and grid[ny][nx] == ">":
            player.location = "Ruins"
            player.x, player.y = SPAWN["ruins"]
            print("You step through the gate into the ancient ruins.")
        elif player.location == "Ruins" and grid[ny][nx] == "<":
            player.location = "Village"
            player.x, player.y = SPAWN["village"]
            print("You return to the village.")
        return True

    def nearby_npcs(self, player) -> list[tuple[str, dict]]:
        return [
            (npc_id, npc)
            for npc_id, npc in NPCS.items()
            if npc["map"] == player.location
            and abs(npc["x"] - player.x) + abs(npc["y"] - player.y) <= 1
        ]

    @staticmethod
    def at_boss(player) -> bool:
        return player.location == "Ruins" and (player.x, player.y) == BOSS_POSITION


def read_key(prompt: str = COMMANDS) -> str:
    if os.name == "nt":
        import msvcrt

        key = msvcrt.getwch()
        if key in ("\x00", "\xe0"):
            msvcrt.getwch()
            return ""
        return key.casefold()
    if not sys.stdin.isatty():
        return input("\n" + prompt + ": ").strip().casefold()[:1]
    import termios
    import tty

    descriptor = sys.stdin.fileno()
    previous = termios.tcgetattr(descriptor)
    try:
        tty.setcbreak(descriptor)
        return sys.stdin.read(1).casefold()
    finally:
        termios.tcsetattr(descriptor, termios.TCSADRAIN, previous)
