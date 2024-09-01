import argparse
import json
import random

from pydantic import BaseModel

import matchmaking as matchmaking
from schema import Job, Lobby, Map, Party, Player


class PydanticEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, BaseModel):
            return o.model_dump()
        else:
            return super().default(o)


def generate_player(
    min_level: int = 1, max_level: int = 300, min_gs: int = 1, max_gs: int = 400
) -> Player:
    "Generated random player with given parameters"
    gear_score = random.randrange(min_gs, max_gs)
    level = random.randrange(min_level, max_level)
    job = random.choice(list(Job))

    player = Player(job=job, level=level, gear_score=gear_score)
    return player


def generate_party(
    num_players: int | None = None, map: Map | None = None, max_size: int | None = None
) -> Party:
    "Generated random party with given parameters"

    # solo/duo/trio
    if not max_size:
        max_size = random.randrange(1, 4)

    if not num_players:
        num_players = random.randrange(1, max_size + 1)
    players = [generate_player() for i in range(num_players)]
    if not map:
        map = random.choice(list(Map))

    party = Party(players=players, map=map, max_size=max_size)
    return party


def party_queuing_generator(current_map=Map.goblin_caves):
    "Generates parties that have 'queued' for a game"
    while True:
        num_parties = random.randrange(0, 2)
        yield [generate_party(map=current_map) for i in range(num_parties)]


def simulator(simulated_secs=600, max_queue_time_secs=300) -> dict:
    """Simulates parties queuing and being matched into a game.

    simulated_secs: how long to simulate matchmaking system running.

    max_queue_time_secs: Max fill time for lobby before force starting game
    """

    # {solo/duo/trio: [lobbies]}
    all_filling_lobbies: dict[int, list[Lobby]] = {1: [], 2: [], 3: []}
    all_started_lobbies: dict[int, list[Lobby]] = {1: [], 2: [], 3: []}
    all_canceled_parties: list[Party] = []

    party_gen = party_queuing_generator()

    for t in range(simulated_secs):
        for lobby_group in all_filling_lobbies.values():
            for lobby in lobby_group:
                lobby.queue_time += 1

        queued_parties = next(party_gen)

        for party in queued_parties:
            l_party_size = party.max_size
            # list of lobbies for the solo/duo/trio queue
            lobby_group = all_filling_lobbies[l_party_size]

            lobby_group, started_lobbies, canceled_parties = (
                matchmaking.matchmake_party(
                    lobby_group,
                    party,
                    max_queue_time_secs=max_queue_time_secs,
                )
            )

            all_filling_lobbies[l_party_size] = lobby_group
            all_started_lobbies[l_party_size] = (
                all_started_lobbies[l_party_size] + started_lobbies
            )
            all_canceled_parties = all_canceled_parties + canceled_parties

    return {
        "started": all_started_lobbies,
        "filling": all_filling_lobbies,
        # parties sent back to menu because no game could be found
        "canceled_parties": all_canceled_parties,
    }


if __name__ == "__main__":

    parser = argparse.ArgumentParser(prog="Dark and Darker Matchmaking Simulator")



    with open("results.json", "w") as f:
        json.dump(simulator(), f, cls=PydanticEncoder, sort_keys=True, indent=2)
