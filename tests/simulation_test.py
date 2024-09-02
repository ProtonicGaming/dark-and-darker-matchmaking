import simulation as simulation
import matchmaking as matchmaking
from schema import Job, Map

import pytest


def test_generate_player():
    min_level = 20
    max_level = 100
    min_gs = 25
    max_gs = 124
    player = simulation.generate_player(
        min_level=min_level, max_level=max_level, min_gs=min_gs, max_gs=max_gs
    )
    assert player.job in Job
    assert min_level <= player.level <= max_level
    assert min_gs <= player.gear_score <= max_gs


def test_generate_party():
    max_party_size = 2
    party = simulation.generate_party(max_size=max_party_size)
    assert len(party.players) > 0
    assert len(party.players) <= max_party_size
    assert party.map in Map


# Fixtures for each argument
@pytest.fixture(scope="session")
def simulated_secs():
    return 300


@pytest.fixture(scope="session")
def max_queue_time_secs():
    return 120


@pytest.fixture(scope="session")
def mmr_method():
    return "max_gs"


@pytest.fixture(scope="session")
def mmr_threshold():
    return 50


@pytest.fixture(scope="session")
def simulator_results(simulated_secs, max_queue_time_secs, mmr_method, mmr_threshold):
    results = simulation.simulator(
        simulated_secs=simulated_secs,
        max_queue_time_secs=max_queue_time_secs,
        mmr_method=mmr_method,
        mmr_threshold=mmr_threshold,
    )

    return results


def test_filling_queue_time(
    simulator_results, simulated_secs, max_queue_time_secs, mmr_method, mmr_threshold
):

    filling = simulator_results["filling"]
    for lobby_party_size, lobbies in filling.items():
        for lobby in lobbies:
            assert lobby.queue_time <= max_queue_time_secs


def test_no_empty_started_parties(
    simulator_results, simulated_secs, max_queue_time_secs, mmr_method, mmr_threshold
):
    started = simulator_results["started"]
    for lobby_party_size, lobbies in started.items():
        for lobby in lobbies:
            assert len(lobby.parties) > 0


def test_started_party_size(
    simulator_results, simulated_secs, max_queue_time_secs, mmr_method, mmr_threshold
):
    started = simulator_results["started"]
    for lobby_party_size, lobbies in started.items():
        for lobby in lobbies:
            for party in lobby.parties:
                assert len(party) == lobby_party_size


def test_mmr_threshold(
    simulator_results, simulated_secs, max_queue_time_secs, mmr_method, mmr_threshold
):

    mmr_fn = matchmaking.MMR_FUNCTIONS[mmr_method]

    filling = simulator_results["filling"]
    for lobby_party_size, lobbies in filling.items():
        for lobby in lobbies:
            max_mmr = max(mmr_fn(party) for party in lobby.parties)
            min_mmr = min(mmr_fn(party) for party in lobby.parties)
            assert (max_mmr - min_mmr) <= mmr_threshold

    started = simulator_results["started"]

    for lobby_party_size, lobbies in started.items():
        for lobby in lobbies:
            max_mmr = max(mmr_fn(party) for party in lobby.parties)
            min_mmr = min(mmr_fn(party) for party in lobby.parties)
            assert (max_mmr - min_mmr) <= mmr_threshold
