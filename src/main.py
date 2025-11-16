from bots.wall_place_bot.bot import WallPlaceBot
from quoridor_env import QuoridorEnv
from bots.ws_bots.basic_bitch_bot import BasicBitchBot


if __name__ == "__main__":
    """This is where you can test out your bot!"""
    game_env = QuoridorEnv()

    player_1 = WallPlaceBot(player_id=0)
    player_2 = BasicBitchBot(player_id=1)

    game_env.game_loop(player_1, player_2, visualise=True)
