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
        num_parties = random.randrange(0, 4)
        yield [generate_party(map=current_map) for i in range(num_parties)]


def simulator(
    simulated_secs=600, max_queue_time_secs=300, mmr_method="max_gs", mmr_threshold=50
) -> dict:
    """Simulates parties queuing and being matched into a game."""

    # {solo/duo/trio: [lobbies]}
    all_filling_lobbies: dict[int, list[Lobby]] = {1: [], 2: [], 3: []}
    all_started_lobbies: dict[int, list[Lobby]] = {1: [], 2: [], 3: []}
    # parties sent back to menu because no game could be found
    all_canceled_parties: list[Party] = []

    party_gen = party_queuing_generator()

    for t in range(simulated_secs):
        queued_parties = next(party_gen)
        process_queued_parties(
            queued_parties,
            all_filling_lobbies,
            max_queue_time_secs,
            mmr_method,
            mmr_threshold,
        )
        update_lobbies(
            all_filling_lobbies,
            all_started_lobbies,
            all_canceled_parties,
            max_queue_time_secs,
        )
        increment_queue_time(all_filling_lobbies)

    return {
        "started": all_started_lobbies,
        "filling": all_filling_lobbies,
        "canceled_parties": all_canceled_parties,
    }


def initialize_lobbies() -> dict[int, list[Lobby]]:
    """Initializes the lobbies dictionary."""
    return {1: [], 2: [], 3: []}


def process_queued_parties(
    queued_parties: list[Party],
    all_filling_lobbies: dict[int, list[Lobby]],
    max_queue_time_secs: int,
    mmr_method: str,
    mmr_threshold: int,
):
    """Processes the queued parties by placing them in lobbies."""
    for party in queued_parties:
        l_party_size = party.max_size
        lobby_group = all_filling_lobbies[l_party_size]
        lobby_group = matchmaking.put_party_in_lobby(
            lobby_group,
            party,
            max_queue_time=max_queue_time_secs,
            mmr_method=mmr_method,
            mmr_threshold=mmr_threshold,
        )
        all_filling_lobbies[l_party_size] = lobby_group


def update_lobbies(
    all_filling_lobbies: dict[int, list[Lobby]],
    all_started_lobbies: dict[int, list[Lobby]],
    all_canceled_parties: list[Party],
    max_queue_time_secs: int,
):
    """Starts or cancels lobbies and updates their status."""
    for l_party_size, lobbies in all_filling_lobbies.items():
        canceled_parties = start_or_cancel_lobbies(lobbies, max_queue_time_secs)
        all_canceled_parties.extend(canceled_parties)

        filling_lobbies, started_lobbies, _ = matchmaking.regroup_lobbies(lobbies)

        all_filling_lobbies[l_party_size] = filling_lobbies
        all_started_lobbies[l_party_size].extend(started_lobbies)


def start_or_cancel_lobbies(
    lobbies: list[Lobby], max_queue_time_secs: int
) -> list[Party]:
    """Attempts to start or cancel lobbies based on queue time."""
    canceled_parties = []
    for lobby in lobbies:
        _, dropped_parties = matchmaking.maybe_start_lobby(lobby, max_queue_time_secs)
        canceled_parties.extend(dropped_parties)

    for lobby in lobbies:
        _, dropped_parties = matchmaking.maybe_cancel_matchmaking(
            lobby, max_queue_time_secs
        )
        canceled_parties.extend(dropped_parties)

    return canceled_parties


def increment_queue_time(all_filling_lobbies: dict[int, list[Lobby]]):
    """Increments the queue time for all lobbies."""
    for lobby_group in all_filling_lobbies.values():
        for lobby in lobby_group:
            lobby.queue_time += 1


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Dark and Darker Matchmaking Simulator"
    )

    parser.add_argument(
        "--simulated_secs",
        type=int,
        default=300,
        help="How long to simulate matchmaking system running.",
    )
    parser.add_argument(
        "--max_queue_time",
        type=int,
        default=300,
        help="How long can a lobby be filling before force starting.",
    )
    parser.add_argument(
        "--mmr_method",
        type=str,
        default="max_gs",
        help="MMR calculation method: Currently 'max_gs' and 'avg_gs'.",
    )
    parser.add_argument(
        "--mmr_threshold",
        type=float,
        default=50,
        help="Maximum MMR difference for two parties to be matchable.",
    )

    args = parser.parse_args()

    results = simulator(
        simulated_secs=args.simulated_secs,
        max_queue_time_secs=args.max_queue_time,
        mmr_method=args.mmr_method,
        mmr_threshold=args.mmr_threshold,
    )

    with open("results.json", "w") as f:
        json.dump(results, f, cls=PydanticEncoder, sort_keys=True, indent=2)
