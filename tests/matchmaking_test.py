import pytest
from pydantic import ValidationError

import matchmaking
from schema import Lobby, Party, Player


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
        party_a, party_b, mmr_fn=matchmaking.max_gearscore_mmr, mmr_threshold=50
    )
    assert matchmaking.are_parties_matchable(
        party_a, party_c, mmr_fn=matchmaking.max_gearscore_mmr, mmr_threshold=50
    )


def test_empty_party():
    with pytest.raises(ValidationError):
        Party(players=[], map="goblin_caves", max_size=0)


def test_single_player_party():
    player = Player(job="fighter", level=10, gear_score=100)
    party = Party(players=[player], map="goblin_caves", max_size=1)
    assert matchmaking.max_gearscore_mmr(party) == player.gear_score
    assert matchmaking.average_gearscore_mmr(party) == player.gear_score


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
