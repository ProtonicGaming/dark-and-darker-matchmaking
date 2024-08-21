import matchmaking
from simulation import generate_party, generate_player
from schema import Party, Player, Lobby, Map, Job

from pydantic import ValidationError
import pytest


def test_max_gearscore_mmr():
    party = Party(
        players=[
            Player(job="fighter", level=10, gear_score=100),
            Player(job="wizard", level=20, gear_score=150),
            Player(job="rogue", level=30, gear_score=200),
        ],
        map="goblin_caves",
        max_size=3,
    )

    assert matchmaking.max_gearscore_mmr(party) == 200


def test_average_gearscore_mmr():
    party = Party(
        players=[
            Player(job="fighter", level=10, gear_score=100),
            Player(job="wizard", level=20, gear_score=150),
            Player(job="rogue", level=30, gear_score=200),
        ],
        map="goblin_caves",
        max_size=3,
    )

    assert matchmaking.average_gearscore_mmr(party) == (100 + 150 + 200) / 3


def test_are_parties_matchable():
    party_a = Party(
        players=[
            Player(job="fighter", level=10, gear_score=100),
            Player(job="wizard", level=20, gear_score=150),
        ],
        map="goblin_caves",
        max_size=2,
    )

    party_b = Party(
        players=[
            Player(job="rogue", level=30, gear_score=200),
            Player(job="bard", level=40, gear_score=250),
        ],
        map="howling_crypts",
        max_size=2,
    )

    party_c = Party(
        players=[
            Player(job="rogue", level=30, gear_score=200),
            Player(job="bard", level=40, gear_score=175),
        ],
        map="howling_crypts",
        max_size=2,
    )

    assert not matchmaking.are_parties_matchable(
        party_a, party_b, mmr_fn=matchmaking.max_gearscore_mmr, threshold=50
    )
    assert matchmaking.are_parties_matchable(
        party_a, party_c, mmr_fn=matchmaking.max_gearscore_mmr, threshold=50
    )


# Optional: Tests for edge cases
def test_empty_party():
    with pytest.raises(ValidationError):
        party = Party(players=[], map="goblin_caves", max_size=0)


def test_single_player_party():
    player = Player(job="fighter", level=10, gear_score=100)
    party = Party(players=[player], map="goblin_caves", max_size=1)
    assert matchmaking.max_gearscore_mmr(party) == player.gear_score
    assert matchmaking.average_gearscore_mmr(party) == player.gear_score


"""
def test_combine_incomplete_parties():
    max_party_size = 3
    parties = [
        generate_party(2, max_party_size),
        generate_party(3, max_party_size),
        generate_party(3, max_party_size),
        generate_party(2, max_party_size),
        generate_party(3, max_party_size),
        generate_party(1, max_party_size),
        generate_party(2, max_party_size),
    ]

    complete_parties, failed_to_complete = matchmaking.combine_incomplete_parties(
        parties, max_party_size
    )

    assert len(failed_to_complete) == 2
    assert len(complete_parties) == 4
"""


def test_successful_attempt_add_party_to_lobby():
    party_a = Party(
        players=[
            Player(job="fighter", level=10, gear_score=100),
            Player(job="wizard", level=20, gear_score=150),
            Player(job="wizard", level=21, gear_score=151),
        ],
        map="goblin_caves",
        max_size=3,
    )

    party_b = Party(
        players=[
            Player(job="rogue", level=30, gear_score=200),
            Player(job="bard", level=40, gear_score=250),
        ],
        map="goblin_caves",
        max_size=3,
    )

    party_c = Party(
        players=[Player(job="rogue", level=31, gear_score=201)],
        map="goblin_caves",
        max_size=3,
    )

    lobby_a = Lobby(parties=[party_a, party_b], map="goblin_caves", party_size=3)
    was_matched, party = matchmaking.attempt_merge_party(lobby_a, party_c)
    assert was_matched


def test_fail_attempt_add_party_to_lobby():
    party_a = Party(
        players=[
            Player(job="fighter", level=10, gear_score=100),
            Player(job="wizard", level=20, gear_score=150),
            Player(job="wizard", level=21, gear_score=151),
        ],
        map="goblin_caves",
        max_size=3,
    )

    party_b = Party(
        players=[
            Player(job="rogue", level=30, gear_score=200),
            Player(job="bard", level=40, gear_score=250),
        ],
        map="goblin_caves",
        max_size=3,
    )

    party_c = Party(
        players=[
            Player(job="rogue", level=30, gear_score=200),
            Player(job="bard", level=40, gear_score=175),
        ],
        map="goblin_caves",
        max_size=3,
    )

    lobby_a = Lobby(parties=[party_a, party_b], map="goblin_caves", party_size=3)

    was_matched, _ = matchmaking.attempt_merge_party(lobby_a, party_c)
    assert not was_matched
