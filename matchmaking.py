from schema import Party, Player, Lobby
from typing import Tuple


# MMR Heirutrics
def max_gearscore_mmr(party: Party) -> float:
    mmr = max([player.gear_score for player in party.players])
    return mmr


def average_gearscore_mmr(party: Party) -> float:
    total_mmr = sum([player.gear_score for player in party.players])
    average_mmr = total_mmr / len(party.players)
    return average_mmr


def are_parties_matchable(
    party_a: Party, party_b: Party, mmr_fn=max_gearscore_mmr, threshold=50
) -> bool:
    "Decides if parties are matchable if mmr is within 'threshold'"

    a_mmr = mmr_fn(party_a)
    b_mmr = mmr_fn(party_b)
    can_match = abs(a_mmr - b_mmr) <= threshold

    return can_match


def can_add_party_to_lobby(
    lobby: Lobby, party: Party, mmr_fn=max_gearscore_mmr, threshold=50
) -> bool:
    """Determines if party can be added to lobby.

    Every party in the lobby must be matchable with new potential party"""

    for lobby_party in lobby.parties:
        if not are_parties_matchable(
            lobby_party, party, mmr_fn=mmr_fn, threshold=threshold
        ):
            return False

    return True


def is_possible_lobby(lobby: Lobby, party: Party) -> bool:
    correct_map = lobby.map == party.map
    correct_size = party.max_size <= lobby.party_size
    correct_mmr = can_add_party_to_lobby(lobby, party)

    return correct_map and correct_size and correct_mmr


"""
def combine_incomplete_parties(parties: list[Party], party_size: int) -> list[Party]:

    complete_parties = [p for p in parties if len(p) == party_size]

    incomplete_parties = [p for p in parties if len(p) < party_size]
    incomplete_parties = sorted(incomplete_parties, key=lambda x: len(x), reverse=True)

    failed_to_complete = []
    combined_parties = []

    # Take first party in list
    # keep attempting to add players until full
    # move on to next incomplete party

    while incomplete_parties:
        currently_filling = incomplete_parties.pop(0)

        for i, other_party in enumerate(incomplete_parties):
            if len(currently_filling) + len(other_party) <= party_size:

                new_players = currently_filling.players + other_party.players
                new_party = Party(
                    players=new_players,
                    map=currently_filling.map,
                    max_size=currently_filling.max_size,
                )

                combined_parties.append(currently_filling)
                combined_parties.append(other_party)
                incomplete_parties.pop(i)

        if len(currently_filling) == party_size:
            complete_parties.append(currently_filling)
        else:
            failed_to_complete.append(current_party)

    return complete_parties, failed_to_complete
"""


def add_party_to_lobbies(lobbies: list[Lobby], party: Party):

    possible_lobbies = [lobby for lobby in lobbies if is_possible_lobby(lobby, party)]

    for lobby in possible_lobbies:
        # attempt combine parties
        #     if not back to the queue
        pass

    # can combine parties?
    # party size must be right
    # map must be right
    None


def attempt_merge_party(lobby: Lobby, new_party: Party) -> Tuple[bool, Party]:
    if len(new_party) == lobby.party_size:
        raise Exception("You messed up")

    for existing_party in lobby.parties:
        if len(existing_party) + len(new_party) <= lobby.party_size:
            existing_party.players = existing_party.players + new_party.players
            return True, new_party

    return False, new_party


def attempt_add_party_to_lobby(
    lobby: Lobby, party: Party, mmr_fn=max_gearscore_mmr, threshold=50
):

    # mmr check
    mmr_check = can_add_party_to_lobby(lobby, party, mmr_fn=mmr_fn, threshold=threshold)
    player_count_check = (lobby.current_player_count() + len(party)) <= lobby.max_players

    if mmr_check and player_count_check:
    #if player_count_check:
        if len(party) == lobby.party_size:
            lobby.parties.append(party)

            return True, party

        else:
            # attempt to combine parties
            was_merged, party = attempt_merge_party(lobby, party)
            return was_merged, party

    else:
        return False, party


# select random map
# select random party size
#    trio cannot queue for solos


# 1. generate random players/parties
# 2. matchmake


# calculate MMR
#     gear score
#     level
#     skill metric


# match based on mmr
# tradeoff close MMR/queue time/full lobbies


# fill trio party:
# 1. find one player, put him in the party
# 2. find more players to fill the party but their MMR cant be too from OG players mmr

# match parties together in a lobby until max wait time
