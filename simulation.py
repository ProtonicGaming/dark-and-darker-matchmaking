from schema import Party, Player, Lobby, Job, Map
import random


def generate_player(
    min_level: int = 1, max_level: int = 300, min_gs: int = 1, max_gs: int = 400
) -> Player:
    gear_score = random.randrange(min_gs, max_gs)
    level = random.randrange(min_level, max_level)
    job = random.choice(list(Job))

    player = Player(job=job, level=level, gear_score=gear_score)
    return player


def generate_party(num_players=None, max_size=3) -> Party:
    if not num_players:
        num_players = random.randrange(1, max_size + 1)
    players = [generate_player() for i in range(num_players)]
    selected_map = random.choice(list(Map))

    # solo/duo/trio
    queue_size = random.randrange(num_players, 3 + 1)
    party = Party(players=players, map=selected_map, max_size=queue_size)
    return party


# Random matchamking queue
# Lobby queue

def main():

    # all mapps
    lobbies = []

    for i in range(100):
        party = generate_party()

    # 1. Party hits queue
    # 2. If can match in existing lobby, match them
    # Otherwise create new lobby
