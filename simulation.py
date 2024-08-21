from schema import Party, Player, Lobby, Job, Map
import random
from queue import PriorityQueue, Queue
from typing import Tuple
import matchmaking as matchmaking
import time
import threading


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


def consumer():
    waiting_lobbies = {1: [], 2: [], 3: []}

    started_lobbies = {1: [], 2: [], 3: []}

    while True:

        #print(started_lobbies)
        """
        for k, v in waiting_lobbies.items():
            print(k, len(v))
        """

        _, party = QUEUE.get()

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
                #print(lobby.current_player_count(), lobby.max_players)
                if lobby.current_player_count() == lobby.max_players:
                    list_of_lobbies.remove(lobby)
                    print("STARTED")
                    started_lobbies[lobby_party_size].append(lobby)

        for k,v in started_lobbies.items():
            print(k, len(v))


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
    main()
