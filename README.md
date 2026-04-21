# Gosino

## Project Description
- **Game Genre:** Stealth, Casino, Roguelike

Gosino is a top-down stealth casino game built with Python and Pygame. You play as a gorilla who must gamble across five different casino mini-games to earn enough money to pay off a growing daily debt — all while avoiding security guards patrolling the floor. Each day the debt increases, the time limit shrinks, and the guards get faster, creating a tense loop of risk and reward.

The game also features a full statistics system that records gameplay data across sessions and visualizes it through in-game graphs and tables, letting players analyze their gambling patterns, guard encounters, and money flow over time.

---

## Installation

To clone this project:
```sh
git clone https://github.com/Jadeung123/Gosino.git
cd Gosino
```

To create and run a Python virtual environment for this project:

**Windows:**
```bat
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

**Mac:**
```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## Running Guide

After activating the Python environment, run the game with:

**Windows:**
```bat
python main.py
```

**Mac:**
```sh
python3 main.py
```

---

## Tutorial / Usage

### Controls
| Key | Action |
|-----|--------|
| `WASD` | Move player |
| `E` | Interact with zone |
| `SPACE` | Perform action (spin, roll, deal) |
| `ESC` | Pause / Exit mini-game |
| `TAB` | Open inventory panel |
| `F1 / F2 / F3` | Use consumable item from inventory |
| `M` | Toggle dice mode (Over / Under) |

### How to Play
1. Launch the game and press **PLAY** from the title screen
2. Walk around the casino floor and press `E` near any game zone to enter it
3. Gamble to earn money — you must pay your **debt** before the timer runs out
4. Reach the **EXIT** door and press `E` to pay your debt and end the day
5. Choose an **upgrade** between days to improve your stats
6. If a guard catches you or your money hits $0, it's **game over**

### Tips
- Guards have vision cones — stay out of their line of sight
- When the casino starts closing, all guards will chase you — head to the exit fast
- Use the shop to buy consumables like Lucky Charm or Insurance before gambling
- Check the Statistics screen from the pause menu or title screen to analyze your performance

---

## Game Features

- **5 Casino Mini-games** — Slots, Blackjack, Roulette, Dice, Case Opening
- **Guard AI** — Guards patrol, alert nearby guards, chase, and search last known positions
- **Day & Debt System** — Each day the debt grows and time limit shrinks
- **Shop System** — Buy consumable and permanent items to gain advantages
- **Upgrade System** — Choose from randomized upgrades between days
- **Inventory Panel** — TAB to view consumables, stats, and owned upgrades
- **Difficulty Scaling** — Guards get faster over time and new elite guards spawn
- **Statistics System** — Gameplay data logged to CSV and visualized in-game with 5 graphs
- **Sound System** — Background music with SFX, volume sliders, and mute toggle
- **Day Transition Screen** — Summary of each day's performance between rounds

---

## Known Bugs

None known at this time.

---

## Unfinished Works

All planned features have been implemented.

---

## External Sources

- **music_casino.ogg(Casino Man)** — https://opengameart.org/content/casino-man - Music
- **music_chase(Free-Jazz/Bebop Chase Music)** — https://opengameart.org/content/free-jazzbebop-chase-music - Music
- **music_victory(On my way)** — https://opengameart.org/ - Music
- **alert.WAV, buy.wav, card_deal.wav, chip.wav, day_complete.wav, exit_zone.wav, footstep.wav, game_over.wav, lose.wav, spin.wav, win.wav** — https://opengameart.org/ - sfx
