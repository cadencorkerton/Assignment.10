# The Shattered Crown

A terminal RPG made for a programming class. It includes instant W/A/S/D map movement, colored maps, account registration and login, TinyDB saves, NPCs, quests, monsters, combat, skills, shops, and character progression.

## Run

```powershell
python -m pip install -r requirements.txt
python main.py
```

Use the terminal for instant movement. The map stays in place and updates the player's position; dialogue appears below it. Register an account, then log in later with the same username and password to continue. Password characters are visible while you type them so password entry works in standard terminals. Passwords are hashed before being saved. Progress is stored in `saves.json` beside the Python files.

## Controls

- **W/A/S/D**: Move immediately without pressing Enter
- **E**: Talk to a nearby person
- **E**: Fight a nearby monster (or step onto its map marker)
- **I**: View inventory
- **C**: View character stats
- **J**: View quests
- **Q**: Save and quit

Monster markers are labeled **G** Goblin, **W** Wolf, **K** Skeleton, and
**T** Troll. Step onto a monster marker to start combat, or stand beside it
and press **E**. During combat, type **A** to attack.

The project has exactly 10 Python files; TinyDB is the only external dependency.
