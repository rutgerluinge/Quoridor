# Researchable Quoridor Bot Tournament

What makes a person at Researchable a Researchable-er you ask?
To me that is:

- Games
- Coding
- Overcomplicating the simple stuff
- Friendly competition
- Fun

Therefore we will try and see who is the best bot maker! Within this readme I will go over the game rules, but also explain how to setup, the rules, what to hand in etc.

Have fun!

---

## Quick Start

### 1) Set up a Python environment

```bash
# (recommended) create and activate a virtual environment, I will be running on python 3.13 with the requirements, with minor issues I will contact you so dont worry too much, but plss no crazy stuff!
python3.13 -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install --upgrade pip

# install dependencies (request for a different package is allowed but try to stay as python pure as possible)
pip install -r requirements.txt
```

### 2) Run the game
You can use this for your own testing!
```bash
python src/main.py
```
or run the tournament (how i will run it after placing all your submitted folders)

```bash
python src/tournament.py
```

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
  - Walls are a resource, you only have 10!
  - **Important**: A wall may not **fully block** all possible paths; both players must always have at least one legal path to their goal row.
- **Movement constraints**:
  - You cannot move through walls.
  - If pawns are adjacent and there is no wall directly behind the opponent’s pawn, you may **jump** over them.
  - If a jump straight ahead is blocked by a wall, you can move **diagonally** around the opponent (if legal per implementation).
- **Starting resources**: Typically, each player starts with **10 walls**. (If your implementation differs, see your config in `src/`.)

For a visual overview and full rules, I would advise the internet (or an llm if you dont like rule books): [Quoridor — Rulebook](https://cdn.1j1ju.com/medias/fe/36/08-quoridor-rulebook.pdf)

---

## Tournament Rules

You and your colleagues will each submit a single bot by extending the base class in `src/bots/bot_template.py`.

- **One file only**: Submit a single Python file containing your bot class: `class MyBot(Bot): ...`
- **Where to inherit from**: `src/bots/bot.py` defines the abstract `Bot` API. Implement the required abstract methods for your bot to run.
- **Required speed**: Your bot’s core decision method (`select_move(...)`) **must complete within 1 seconds** (on my machine lol) I might change this if i see that it is a problem.
- **Do not modify the engine**: You may only edit your own bot file. Engine/runner changes are not allowed for submissions.
- **Tournament format**:
  - **Round-robin**: Each bot plays every other bot multiple times.
  - **Number of games**: **100 games per pairing**
  - **Scoring**: Win = 1, Loss = 0. (Draws, if any exist in the engine, count as 0.5 (for example max number of turns (config)))
  - **Winner**: The bot with the **highest win percentage** across all its games is crowned the winner. (maybe live final?)

 I will run the tournament: make sure your bot file imports cleanly with no extra installation steps beyond `requirements.txt`.

---

## Implementing Your Bot

### Step-by-Step Guide

**Step 1:** Create a folder in `src/bots/` named after yourself or your bot.

**Step 2:** Create a new Python file named `bot.py` in your folder and inherit from `QuoridorBot`:

```python
class QuoridorBot(ABC):
    """Abstract Class to follow for your own bot creationg"""

    # this will be initialised to either be player 1 (idx =0) thus start player,
    # or player 2 (idx = 1) you have a differnet start pos and goal pos
    def __init__(self, player_id: int):
        self.player_id = player_id

    @staticmethod
    @abstractmethod
    def __str__() -> str:
        """Use an original name!"""
        raise NotImplementedError

    @abstractmethod
    def reset(self) -> None:
        """Reset any internal state between games, if needed. This gets called instead of creating a new bot instance, such that you could use tactics for countering your opponents playstyle"""
        pass

    @abstractmethod
    def select_move(self, state: GraphState, legal_actions: List[Action]) -> Action:
        """Main logic of your quoridor bot"""
        raise NotImplementedError

```

This file needs to be in its own folder in `src/bots/your_folder_name/`
In this folder you are allowed to add additional files, just dont do sketchy stuff or too many work arounds we are trying to keep it low key. Preferably keep it within your bot python script, and maybe a trained model if you actually took the time to try that out lol.

## Note:
If your call of select_move times out, throws an illegal move (not in legal_actions) or just makes a mistake, you automatically lose the game, make sure that doesn't happen!

I added a derpy example in **`src/bots/wall_place_bot`**  such that you can see an example


## Submission Checklist

- I created a folder with the name of **myself** or my **genius bot**
- I added a python file with the name: **`bot.py`** in this folder
- I inherited **`bot.py`** from the **`QuordiorBot`** abstract class in **`template_bot.py`**
- I can add files in my folder that my bot uses, but this is certainly not necessary

## Issues

Might there be any problems, please let me know or PR, I probably overlooked some logic or something.

If you have any suggestions or remarks for the format please let me know!
