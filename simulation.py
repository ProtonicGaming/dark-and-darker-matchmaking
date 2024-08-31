from schema import Party, Player, Lobby, Job, Map
import random
from queue import PriorityQueue, Queue
from typing import Tuple
import matchmaking as matchmaking
import time
import threading
import json

from pydantic import BaseModel


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


def simulator(simulated_secs=300, max_queue_time_secs=30) -> dict:

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
            # all_canceled_lobbies[l_party_size].append(canceled_parties)

    return {
        "started": all_started_lobbies,
        "waiting": all_waiting_lobbies,
        "canceled_parties": all_canceled_parties,
        # "canceled": all_canceled_lobbies,
    }


def consumer():
    waiting_lobbies = {1: [], 2: [], 3: []}

    started_lobbies = {1: [], 2: [], 3: []}

    while True:

        # print(started_lobbies)
        """
        for k, v in waiting_lobbies.items():
            print(k, len(v))
        """

        priority, party = QUEUE.get()

        lobby_party_size = party.max_size

        possible_lobbies = waiting_lobbies[lobby_party_size]

        if not possible_lobbies:
            # create lobby
            new_lobby = Lobby(parties=[party], map=party.map, party_size=party.max_size)

            possible_lobbies.append(new_lobby)

        else:
            successfully_added_party = False
            for lobby in possible_lobbies:
                # attempt to add to existing lobbies
                was_merged, _ = matchmaking.attempt_add_party_to_lobby(lobby, party)
                if was_merged:
                    print("MERGED")
                    successfully_added_party = True
                    break

            # failed to add to lobby - create new lobby
            if not successfully_added_party:

                new_lobby = Lobby(
                    parties=[party], map=party.map, party_size=party.max_size
                )
                possible_lobbies.append(new_lobby)

        for lobby_party_size, list_of_lobbies in waiting_lobbies.items():
            for lobby in list_of_lobbies:
                # print(lobby.current_player_count(), lobby.max_players)
                if lobby.current_player_count() == lobby.max_players:
                    list_of_lobbies.remove(lobby)
                    print("STARTED")
                    started_lobbies[lobby_party_size].append(lobby)

        if priority == 299:
            for k, v in started_lobbies.items():
                if v:
                    print(k, v[0])


def main():
    producer_thread = threading.Thread(target=producer, daemon=False)
    consumer_thread = threading.Thread(target=consumer, daemon=False)

    # Start the threads
    producer_thread.start()
    consumer_thread.start()

    # Run for a while to see the producer-consumer interaction
    try:
        time.sleep(10)  # Run the system for 10 seconds
    except KeyboardInterrupt:
        print("Interrupted by user")


if __name__ == "__main__":
    with open("results.json", "w") as f:
        json.dump(simulator(), f, cls=PydanticEncoder, sort_keys=True, indent=2)
