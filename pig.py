import argparse
import random
import time


random.seed(0)

WINNING_SCORE = 100
TIME_LIMIT = 60
COMPUTER_HOLD_LIMIT = 25


class Die:
    def __init__(self, sides=6):
        self.sides = sides

    def roll(self):
        return random.randint(1, self.sides)


class Player:
    def __init__(self, name):
        self.name = name
        self.score = 0

    def add_points(self, points):
        self.score += points

    def reset(self):
        self.score = 0

    def decide(self, turn_total):
        raise NotImplementedError


class HumanPlayer(Player):
    def decide(self, turn_total):
        while True:
            choice = input(f'{self.name}, roll or hold? (r/h): ').strip().lower()
            if choice in ('r', 'h'):
                return choice
            print("Please enter 'r' to roll or 'h' to hold.")


class ComputerPlayer(Player):
    def decide(self, turn_total):
        hold_at = min(COMPUTER_HOLD_LIMIT, WINNING_SCORE - self.score)
        if turn_total >= hold_at:
            print(f'{self.name} (computer) decides to hold.')
            return 'h'
        print(f'{self.name} (computer) decides to roll.')
        return 'r'


class PlayerFactory:
    PLAYER_TYPES = {
        'human': HumanPlayer,
        'computer': ComputerPlayer,
    }

    def create_player(self, player_type, name):
        player_class = self.PLAYER_TYPES.get(player_type.lower())
        if player_class is None:
            raise ValueError(f'Unknown player type: {player_type}')
        return player_class(name)


class Game:
    def __init__(self, player_types, die=None):
        factory = PlayerFactory()
        self.players = [factory.create_player(player_type, f'Player {number}')
                        for number, player_type in enumerate(player_types, start=1)]
        self.die = die if die is not None else Die()

    def reset(self):
        for player in self.players:
            player.reset()

    def show_scores(self):
        scores = ', '.join(f'{player.name}: {player.score}'
                           for player in self.players)
        print(f'Scores: {scores}')

    def start_turn(self, player):
        print(f"\n{player.name}'s turn")
        self.show_scores()

    def take_step(self, player, turn_total):
        roll = self.die.roll()

        if roll == 1:
            print(f'{player.name} rolled a 1. Turn over with no points. '
                  f'Total score: {player.score}')
            return 0, True

        turn_total += roll
        print(f'{player.name} rolled a {roll}. Turn total: {turn_total}. '
              f'Total score: {player.score}')

        if player.decide(turn_total) == 'h':
            player.add_points(turn_total)
            print(f'{player.name} holds with {turn_total} points. '
                  f'Total score: {player.score}')
            return turn_total, True

        return turn_total, False

    def play_turn(self, player):
        self.start_turn(player)
        turn_total, turn_over = 0, False
        while not turn_over:
            turn_total, turn_over = self.take_step(player, turn_total)

    def announce_winner(self, player):
        print(f'\n{player.name} wins with {player.score} points!')
        self.show_scores()

    def play(self):
        self.reset()

        while True:
            for player in self.players:
                self.play_turn(player)
                if player.score >= WINNING_SCORE:
                    self.announce_winner(player)
                    return player


class TimedGameProxy:
    def __init__(self, game, time_limit=TIME_LIMIT):
        self.game = game
        self.time_limit = time_limit
        self.start_time = None

    def __getattr__(self, name):
        return getattr(self.game, name)

    def time_left(self):
        return self.time_limit - (time.monotonic() - self.start_time)

    def time_is_up(self):
        return self.time_left() <= 0

    def play_turn(self, player):
        self.game.start_turn(player)
        print(f'Time left: {max(0, round(self.time_left()))} seconds')
        turn_total, turn_over = 0, False
        while not turn_over and not self.time_is_up():
            turn_total, turn_over = self.game.take_step(player, turn_total)

    def end_on_time(self):
        print('\nTime is up!')
        top_score = max(player.score for player in self.game.players)
        leaders = [player for player in self.game.players
                   if player.score == top_score]

        if len(leaders) > 1:
            print(f'The game ends in a tie at {top_score} points.')
            self.game.show_scores()
            return None

        self.game.announce_winner(leaders[0])
        return leaders[0]

    def play(self):
        self.game.reset()
        self.start_time = time.monotonic()
        print(f'Timed game: {self.time_limit} seconds on the clock.')

        while True:
            for player in self.game.players:
                if self.time_is_up():
                    return self.end_on_time()
                self.play_turn(player)
                if player.score >= WINNING_SCORE:
                    self.game.announce_winner(player)
                    return player


def main():
    parser = argparse.ArgumentParser(description='Play the dice game Pig.')
    parser.add_argument('--player1', type=str.lower, default='human',
                        choices=PlayerFactory.PLAYER_TYPES,
                        help='human or computer (default: human)')
    parser.add_argument('--player2', type=str.lower, default='human',
                        choices=PlayerFactory.PLAYER_TYPES,
                        help='human or computer (default: human)')
    parser.add_argument('--timed', action='store_true',
                        help='end the game after one minute')
    args = parser.parse_args()

    game = Game([args.player1, args.player2])
    if args.timed:
        game = TimedGameProxy(game)
    game.play()


if __name__ == '__main__':
    main()
