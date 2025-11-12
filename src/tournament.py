import importlib.util
import inspect
import os
import sys
from argparse import ArgumentParser
from types import ModuleType
from typing import Dict, List, Type, get_type_hints, Optional

import numpy as np
import pandas as pd

from action import Action
from bots.template_bot import QuoridorBot
from configs import TournamentConfig
from quoridor_env import QuoridorEnv


def load_module_from_path(path: str, module_name: str) -> ModuleType:
    """
    Dynamically load a Python module from a file path, using a custom module name.
    """
    path = os.path.abspath(path)
    spec = importlib.util.spec_from_file_location(module_name, path)
    if not spec or not spec.loader:
        raise ImportError(f"Cannot load module from {path}")

    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)
    return mod


def find_single_bot_class(mod: ModuleType) -> Type[QuoridorBot]:
    """
    Find exactly one concrete QuoridorBot subclass defined in `mod`.
    Raises if zero or multiple candidates are found.
    """
    candidates: List[Type[QuoridorBot]] = [
        cls
        for _, cls in inspect.getmembers(mod, inspect.isclass)
        if issubclass(cls, QuoridorBot)
        and cls is not QuoridorBot
        and cls.__module__ == mod.__name__
    ]

    if not candidates:
        raise LookupError(
            f"No QuoridorBot subclass found in {getattr(mod, '__file__', mod.__name__)}."
        )
    if len(candidates) > 1:
        names = ", ".join(c.__name__ for c in candidates)
        raise LookupError(
            f"Multiple QuoridorBot subclasses in {getattr(mod, '__file__', mod.__name__)}: {names}. "
            "Keep only one subclass per file."
        )
    return candidates[0]


def load_bot_class(path: str, module_name: str) -> Type[QuoridorBot]:
    """
    Load a bot class from a file path.
    Enforces: exactly one QuoridorBot subclass in that module.
    """
    mod = load_module_from_path(path, module_name=module_name)
    bot_cls = find_single_bot_class(mod)
    return bot_cls


def is_valid_bot(bot_cls: Type[QuoridorBot]) -> bool:
    """
    Check if a class implements the required QuoridorBot interface
    (lightweight sanity check; not a full type checker).
    """
    if not inspect.isclass(bot_cls):
        print(f"{bot_cls!r} is not a class.")
        return False

    if not issubclass(bot_cls, QuoridorBot):
        print(f"{bot_cls.__name__} does not inherit from QuoridorBot.")
        return False

    # Required methods and their return annotations (if present)
    required_methods = {
        "__str__": str,
        "select_move": Action,
    }

    for method_name, expected_return in required_methods.items():
        method = getattr(bot_cls, method_name, None)
        if method is None or not callable(method):
            print(f"{bot_cls.__name__} is missing method: {method_name}")
            return False

        # Try to inspect type hints; if none, we don't fail hard
        try:
            hints = get_type_hints(method)
        except Exception:
            hints = {}

        actual_ret = hints.get("return")
        if actual_ret is not None and actual_ret is not expected_return:
            print(
                f"{bot_cls.__name__}.{method_name}() should return "
                f"{expected_return}, found {actual_ret}"
            )
            return False

        if method_name == "select_move":
            # Check parameter names: (self, state, legal_actions)
            sig = inspect.signature(method)
            expected_params = ["self", "state", "legal_actions"]
            if list(sig.parameters.keys()) != expected_params:
                print(
                    f"{bot_cls.__name__}.select_move should have parameters "
                    f"(self, state, legal_actions), found {list(sig.parameters.keys())}"
                )
                return False

    return True


class QuoridorTournament:
    def __init__(self, bot_folder: str, result_csv: str, visualise: bool) -> None:
        self.settings = TournamentConfig()

        self.bot_folder = bot_folder
        self.result_csv = result_csv
        self.rounds = self.settings.rounds
        self.visualise = visualise

        if self.rounds % 2 != 0:
            # Uneven rounds makes first-move advantage skewed
            raise ValueError("Round count must be even to make outcome fair.")

        # Maps bot name -> bot class (subclass of QuoridorBot)
        self.bot_classes: Dict[str, Type[QuoridorBot]] = {}

        # Winrate matrix (rows/cols = bot names)
        self.scores: Optional[pd.DataFrame] = None

    def load_or_create_scores(self) -> None:
        """
        Load an existing results CSV if present, otherwise create a new
        winrate table (NaN entries = not yet played).
        Automatically adds rows/cols for new bots.
        """
        bot_names = list(self.bot_classes.keys())
        path = self.result_csv

        if os.path.exists(path):
            df = pd.read_csv(path, index_col=0)

            # Ensure all loaded bots are represented
            existing_bots = set(df.index)
            new_bots = [b for b in bot_names if b not in existing_bots]

            if new_bots:
                print(f"Adding {len(new_bots)} new bots: {', '.join(new_bots)}")
                for bot in new_bots:
                    # New rows/cols initialised to NaN (unplayed)
                    df.loc[bot] = np.nan
                    df[bot] = np.nan

            # Reindex to current bot order (both rows and columns)
            df = df.reindex(index=bot_names, columns=bot_names)
            self.scores = df
            print(f"Loaded existing scores from {path}")
        else:
            # Fresh table: all matchups unplayed
            self.scores = pd.DataFrame(np.nan, index=bot_names, columns=bot_names)
            print(f"Created new scores table for {len(bot_names)} bots.")

    # ----- Match playing -----

    def n_matches(
        self, bot_1_cls: Type[QuoridorBot], bot_2_cls: Type[QuoridorBot]
    ) -> float:
        """
        Play `self.rounds` games between two bots, alternating who starts.
        Returns:
            float: win rate (0–1) of bot_1.
        """
        env = QuoridorEnv()
        wins_bot1 = 0

        # Create bot instances once and reuse, calling reset() before each game
        bot1 = bot_1_cls(0)
        bot2 = bot_2_cls(1)

        for i in range(self.rounds):
            bot1.reset()
            bot2.reset()
            env.reset()

            # Alternate who starts
            if i % 2 == 0:
                p1, p2 = bot1, bot2
                bot1_id = 0
            else:
                p1, p2 = bot2, bot1
                bot1_id = 1  # bot_1 plays as player 2 here

            winner_player_id: int = env.game_loop(p1, p2, visualise=self.visualise)

            if winner_player_id == bot1_id:
                wins_bot1 += 1

            if (
                winner_player_id == -1
            ):  # draw because of timeout (probably random moves)
                wins_bot1 += 0.5

        return wins_bot1 / self.rounds

    def run_all_rounds(self) -> None:
        """
        Iterate over all bot pairs and play missing matchups.
        Updates self.scores and writes to CSV after each result.
        """
        if (
            not self.bot_classes
            or self.scores is None
            or not isinstance(self.scores, pd.DataFrame)
        ):
            raise RuntimeError(
                "First initialise the bots and scores DataFrame before running!"
            )

        bot_names = list(self.scores.index)

        for i, row_bot in enumerate(bot_names):
            for j, col_bot in enumerate(bot_names):
                # Skip same-bot matchup or lower triangle (matrix is symmetric)
                if i >= j:
                    continue

                value = self.scores.at[row_bot, col_bot]

                # If already played (not NaN), skip
                if pd.notna(value):
                    continue

                row_bot_winrate = self.n_matches(
                    bot_1_cls=self.bot_classes[row_bot],
                    bot_2_cls=self.bot_classes[col_bot],
                )
                col_bot_winrate = 1.0 - row_bot_winrate

                print(
                    f"{row_bot} vs {col_bot}: "
                    f"{row_bot_winrate:.2%} - {col_bot_winrate:.2%}"
                )

                self.scores.at[row_bot, col_bot] = row_bot_winrate
                self.scores.at[col_bot, row_bot] = col_bot_winrate

                self.scores.to_csv(self.result_csv)

    # ----- Bot discovery & validation -----

    def read_and_validate_bots(self) -> None:
        """
        Discover bots in subfolders of self.bot_folder.

        Expected structure:

            self.bot_folder/
                bot_template.py
                student_1_bot/
                    bot.py      # or any .py file containing a QuoridorBot
                    <models, etc.>
                student_2_bot/
                    bot2.py
                    ...

        Rule: we register at most **one bot per folder**.
        The folder name is used as the bot label (e.g. 'student_1_bot').
        """
        for entry in os.scandir(self.bot_folder):
            if not entry.is_dir():
                continue

            folder_name = entry.name
            folder_path = entry.path

            # Find all .py files in the student's folder
            py_files = [
                f
                for f in os.listdir(folder_path)
                if f.endswith(".py") and not f.startswith("__")
            ]

            if not py_files:
                # Nothing to load from this folder
                continue

            bot_registered_for_folder = False

            for file_name in py_files:
                full_path = os.path.join(folder_path, file_name)

                # Unique module name to avoid collisions in sys.modules
                module_base = os.path.splitext(file_name)[0]
                module_name = f"quoridor_{folder_name}_{module_base}"

                try:
                    bot_cls = load_bot_class(full_path, module_name=module_name)
                except Exception as e:
                    print(f"Failed to load bot from {folder_name}/{file_name}: {e}")
                    continue

                if not is_valid_bot(bot_cls):
                    print(
                        f"Bot in {folder_name}/{file_name} is not valid and was skipped."
                    )
                    continue

                # Use folder name as label so students can use the same class name
                bot_label = folder_name

                if bot_label in self.bot_classes:
                    print(
                        f"Warning: bot label '{bot_label}' already registered; "
                        f"skipping extra bot in {folder_name}/{file_name}."
                    )
                    continue

                self.bot_classes[bot_label] = bot_cls
                bot_registered_for_folder = True
                print(f"Registered bot '{bot_label}' from {folder_name}/{file_name}")

                # Enforce: at most one bot per folder
                break

            if not bot_registered_for_folder:
                print(f"No valid bot found in folder '{folder_name}'.")


# ---------- Start ----------

if __name__ == "__main__":
    parser = ArgumentParser(description="Run a Quoridor bot tournament.")
    parser.add_argument(
        "--src_folder",
        "-f",
        type=str,
        required=True,
        help="Folder containing bot .py files.",
    )
    parser.add_argument(
        "--result_csv", "-r", type=str, required=True, help="Path to results CSV."
    )
    parser.add_argument(
        "--visualise", "-v", action="store_true", help="Visualise games in the console."
    )

    args = parser.parse_args()

    tournament = QuoridorTournament(
        bot_folder=args.src_folder,
        result_csv=args.result_csv,
        visualise=args.visualise,
    )

    tournament.read_and_validate_bots()
    if not tournament.bot_classes:
        print("No valid bots found. Exiting.")
        sys.exit(1)

    tournament.load_or_create_scores()
    tournament.run_all_rounds()
