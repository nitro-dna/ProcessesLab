# Python Multi-Process Dungeon Crawler

## Overview
This is a multi-process dungeon crawler game built in Python.
The game uses concurrent processes communicating via pipes and signals to manage a party of adventurers exploring a dungeon,
fighting monsters, and collecting loot. It requires two separate terminal windows to run.

## Architecture
The game consists of three main components:
* **The Dungeon Master (`dm.py`)**: Manages the monsters, their health pools, and dungeon validation.
    It uses named pipes (FIFOs) to communicate with the Mentor to calculate combat hits and validate movements.
* **The Mentor (`mentor.py`)**: Acts as the user interface and controller.
    It reads the party configuration, spawns individual adventurer processes using `os.fork()`, 
    and routes your terminal commands to them via data pipes.
* **The Adventurer (`adventurer.py`)**: Each character runs as an independent process.
    They track their own health, mana, and gold, responding to text commands from the Mentor and system signals.

## Setup and Launch Instructions
You need three configuration files to play: a dungeon map file, a party list file, and a monsters list file.

1. **Start the Dungeon Master:**
   Open your first terminal and run the following command:
   `python3 dm.py -dungeon <map_file> -monsters <monsters_file>`
   Wait for the console to display that it is waiting for the Mentor connection.

2. **Start the Mentor:**
   Open a second terminal and run the following command:
   `python3 mentor.py -dungeon <map_file> -party <party_file> <YourMentorName>`

## How to Play
Control your party from the Mentor terminal[cite: 3]. You can issue commands 
to a specific adventurer ID (e.g., `1`, `2`) or to the entire party using `all`.

### Available Commands:
* `print`: Displays the dungeon layout, revealing the fog of war and showing adventurer positions.
* `pos <id/all>`: Shows the current row and column coordinates of the target(s).
* `health <id/all>`: Displays the current health of the target(s).
* `mv <id/all> <direction>`: Moves the adventurer `up`, `down`, `left`, or `right`.
   Each movement costs 2 mana.
* `unbox <id/all>`: Spends 2 mana to open a box at the adventurer's location. 
   Boxes randomly grant or drain health, mana, or gold.
* `petrify <id/all>`: Freezes an adventurer in place using the `SIGTSTP` signal.
* `depetrify <id/all>`: Unfreezes an adventurer using the `SIGCONT` signal.
* `exit`: Safely terminates all adventurer processes, closes pipes, and exits the game.

### Gameplay Mechanics
* **Health Drain**: Time is against you.
 Adventurers automatically lose 1 health point every 2 seconds due to an internal timer. 
* **Petrification**: Using the `petrify` command halts the continuous health drain while the adventurer is frozen,
     allowing you to strategize[cite: 1].
* **Combat**: Combat is movement-based. Stepping on a monster's tile deals 10 damage to the monster. 
    If the monster survives, it hits back, reducing the adventurer's health by 10.