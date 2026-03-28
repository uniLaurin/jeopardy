import startscreen
import settings
import game
import scores
import resources as r


def main():
    startscreen.run()
    r.ensure_default_questionset()
    settings.run()
    r.reset_game_state()
    game.run()
    scores.run()


if __name__ == "__main__":
    main()
