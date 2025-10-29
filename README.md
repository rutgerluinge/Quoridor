# Quoridor Bot Tournament

Welcome! 👋

This repository lets you play Quoridor and run a friendly—yet fiercely competitive—bot tournament with your colleagues. Build a bot, battle everyone else, and claim eternal office glory.

---

## Quick Start

### 1) Set up a Python environment

```bash
# (recommended) create and activate a virtual environment
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# install dependencies
pip install -r requirements.txt
```

### 2) Run the game

```bash
python src/main.py
```

> This should launch/drive the game using the code in `src/`.

---

## What is Quoridor? (Rules Overview)

Quoridor is a two-player abstract strategy game on a 9×9 board. Each player starts on opposite sides and tries to be the first to reach the row on the far side.

- **Objective**: Reach the opponent’s starting side first.
- **Your options each turn**:
  1. **Move your pawn** one space (up/down/left/right), or jump over when opposing a pawn directly (and it is legal legal).
  2. **Place a wall** to slow down your opponent.
- **Walls**:
  - Walls occupy two edges between squares (they’re placed between cells, horizontally or vertically).
  - Walls **cannot** overlap, cross illegally, or be placed off-grid.
  - **Important**: A wall may not **fully block** all possible paths; both players must always have at least one legal path to their goal row.
- **Movement constraints**:
  - You cannot move through walls.
  - If pawns are adjacent and there is no wall directly behind the opponent’s pawn, you may **jump** over them.
  - If a jump straight ahead is blocked by a wall, you can move **diagonally** around the opponent (if legal per implementation).
- **Starting resources**: Typically, each player starts with **10 walls**. (If your implementation differs, see your config in `src/`.)

> Note: Exact edge cases (diagonal jump rules, wall count, etc.) follow the rules implemented in this codebase. When in doubt, rely on the engine’s legality checks.

---

## Tournament Rules

You and your colleagues will each submit a single bot by extending the base class in `src/bots/bot.py`.

- **One file only**: Submit a single Python file containing your bot class: `class MyBot(Bot): ...`
- **Where to inherit from**: `src/bots/bot.py` defines the abstract `Bot` API. Implement the required abstract methods for your bot to run.
- **Required speed**: Your bot’s core decision method (`select_move(...)`) **must complete within 10 seconds** per move on the organizer’s Lenovo ThinkPad.
- **Do not modify the engine**: You may only edit your own bot file. Engine/runner changes are not allowed for submissions.
- **Tournament format**:
  - **Round-robin**: Each bot plays every other bot multiple times.
  - **Number of games**: **20 games per pairing** — recommended split: **10 as first player, 10 as second** to balance turn order.
  - **Scoring**: Win = 1, Loss = 0. (Draws, if any exist in the engine, count as 0.5.)
  - **Winner**: The bot with the **highest win percentage** across all its games is crowned the winner.
  - **Ties**: If there is a tie in win percentage, resolve with (in order):
    1. Head‑to‑head record among tied bots
    2. Sonneborn–Berger (sum of beaten opponents’ scores) or simple strength-of-schedule, depending on the organizer’s preference
    3. If still tied, a 10‑game playoff per pairing (balanced colors)

> The organizer will run the tournament; make sure your bot file imports cleanly with no extra installation steps beyond `requirements.txt`.

---

## Implementing Your Bot

Create a new Python file (or copy a template) for your bot and inherit from `QuoridorBot`:

```python
class QuoridorBot(ABC):
    """Abstract Class to follow for your own bot creationg"""

    # this will be initialised to either be player 1 (idx =0) thus start player,
    # or player 2 (idx = 1) you have a differnet start pos and goal pos
    def __init__(self, player_id: int):
        self.player_id = player_id

    @abstractmethod
    def select_move(self, state: GraphState, legal_actions: List[Action]) -> Action:
        """Subclasses must implement this."""
        raise NotImplementedError
```

**Important notes**

- Your file can be any length; performance is what matters.
- Don’t spawn external processes or require extra packages beyond `requirements.txt`.
- No or minimal logs.

---

<!-- ## Running Matches & Tournaments

The exact command may vary depending on how the organizer wired the CLI in `src/`. If not provided, a typical pattern is:

```bash
# to pit two bots against each other
python src/main.py --bot-a path/to/BotA.py --bot-b path/to/BotB.py --games 20

# to run a full round-robin over a folder of bots
python src/main.py --bots-folder bots_submissions/ --games-per-pair 20
```

> If your `main.py` uses different flags, check its `--help` message or the code. -->

## Submission Checklist

- `class MyBot(Bot)` defined in a **single Python file**.
- All required abstract methods implemented (notably `select_move(...)`).
- No edits outside your bot file.
- Runs with `pip install -r requirements.txt` on a clean machine.
- `select_move(...)` stays **under 10 seconds** per move.

## License / Credits

Created by Rutger Luinge
