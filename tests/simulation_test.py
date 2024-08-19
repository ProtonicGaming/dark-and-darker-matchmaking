import simulation as simulation
from schema import Job, Map


def test_generate_player():
    min_level = 20
    max_level = 100
    min_gs = 25
    max_gs = 124
    player = simulation.generate_player(min_level=min_level, max_level=max_level, min_gs=min_gs, max_gs=max_gs)
    assert player.job in Job
    assert min_level <= player.level <= max_level
    assert min_gs <= player.gear_score <= max_gs

def test_generate_party():
    max_party_size = 2
    party = simulation.generate_party(max_size=max_party_size)
    assert len(party.players) > 0
    assert len(party.players) <= max_party_size
    assert party.map in Map
