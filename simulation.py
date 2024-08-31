import json
import random
from queue import PriorityQueue, Queue
from typing import Tuple

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
    gear_score = random.randrange(min_gs, max_gs)
    level = random.randrange(min_level, max_level)
    job = random.choice(list(Job))

    player = Player(job=job, level=level, gear_score=gear_score)
    return player


def generate_party(
    num_players: int | None = None, map: Map | None = None, max_size: int | None = None
) -> Party:

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


# QUEUES = {1: PriorityQueue(), 2: PriorityQueue(), 3: PriorityQueue()}

QueueType = Queue[Tuple[int, Party]]
QUEUE: QueueType = PriorityQueue()


def producer():
    current_map = random.choice(list(Map))

    for queue_time in range(300):
        new_party_queued = random.choices([True, False], weights=[0.25, 0.75])

        if new_party_queued:
            new_party = generate_party(map=current_map)
            priority = queue_time  # Simulated queue time

            QUEUE.put((priority, new_party))


def party_queing_generator(current_map=Map.goblin_caves):
    t = 0
    while True:
        new_party_queued = random.choices([True, False], weights=[0.5, 0.5])[0]
        if new_party_queued:
            new_party = generate_party(map=current_map)
            yield new_party
            t += 1
        else:
            yield None


def simulator(simulated_secs=11663, max_queue_time_secs=64) -> dict:

    all_waiting_lobbies: dict[int, list[Lobby]] = {1: [], 2: [], 3: []}
    all_started_lobbies: dict[int, list[Lobby]] = {1: [], 2: [], 3: []}
    # all_canceled_lobbies = {1: [], 2: [], 3: []}

    all_canceled_parties: list[Party] = []

    for t in range(simulated_secs):

        gen = party_queing_generator()

        for lobby_group in all_waiting_lobbies.values():
            for lobby in lobby_group:
                lobby.queue_time += 1

        possibly_queued_party = next(gen)

        if possibly_queued_party:
            l_party_size = possibly_queued_party.max_size
            lobby_group = all_waiting_lobbies[l_party_size]

            lobby_group, started_lobbies, canceled_parties = (
                matchmaking.matchmake_party(
                    lobby_group,
                    possibly_queued_party,
                    max_queue_time_secs=max_queue_time_secs,
                )
            )

            all_waiting_lobbies[l_party_size] = lobby_group
            all_started_lobbies[l_party_size] = (
                all_started_lobbies[l_party_size] + started_lobbies
            )
            all_canceled_parties = all_canceled_parties + canceled_parties

    return {
        "started": all_started_lobbies,
        "waiting": all_waiting_lobbies,
        "canceled_parties": all_canceled_parties,
        # "canceled": all_canceled_lobbies,
    }


if __name__ == "__main__":
    with open("results.json", "w") as f:
        json.dump(simulator(), f, cls=PydanticEncoder, sort_keys=True, indent=2)
