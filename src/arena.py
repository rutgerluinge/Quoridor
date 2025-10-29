from src.bots.bot import QuoridorBot
from src.bots.random_bot import RandomBot
from src.quoridor_env import QuoridorEnv
from src.config import Config


def start_single_game(bot: QuoridorBot, bot2: QuoridorBot):
    pass


def battle(bot: type[QuoridorBot], bot2: type[QuoridorBot], n_games: int):
    config = Config()
    if n_games % 2 == 1 or n_games <= 0:
        raise ValueError("Uneven number of games will make it unfair")

    for game_index in range(n_games / 2):
        result = start_single_game(
            bot=bot(player_id=config.P1), bot2=bot2(player_id=config.P2)
        )
        result = start_single_game(bot=bot(player_id=config.P2), bot2=bot2(config.P1))


battle(RandomBot, RandomBot, n_games=4)
