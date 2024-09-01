from typing import Tuple

from schema import Lobby, LobbyStatus, Party


# MMR Heirutrics
def max_gearscore_mmr(party: Party) -> float:
    mmr = max(player.gear_score for player in party.players)
    return mmr


def average_gearscore_mmr(party: Party) -> float:
    total_mmr = sum(player.gear_score for player in party.players)
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
    player_count_check = (
        lobby.current_player_count() + len(party)
    ) <= lobby.max_players

    if mmr_check and player_count_check:
        # if player_count_check:
        if len(party) == lobby.party_size:
            lobby.parties.append(party)

            return True, party

        else:
            # attempt to combine parties
            was_merged, party = attempt_merge_party(lobby, party)
            return was_merged, party

    else:
        return False, party


def put_party_in_lobby(filling_lobbies: list[Lobby], party: Party) -> list[Lobby]:
    """Adds a party from the matchmaking queue to lobbies being filled."""

    if not filling_lobbies:
        # create lobby
        new_lobby = Lobby(parties=[party], map=party.map, party_size=party.max_size)
        filling_lobbies.append(new_lobby)
    else:
        successfully_added_party = False
        for lobby in filling_lobbies:
            # attempt to add to existing lobbies
            was_merged, _ = attempt_add_party_to_lobby(lobby, party)
            if was_merged:
                successfully_added_party = True
                break
        # failed to add to lobby - create new lobby
        if not successfully_added_party:
            new_lobby = Lobby(parties=[party], map=party.map, party_size=party.max_size)
            filling_lobbies.append(new_lobby)

    return filling_lobbies


def maybe_start_lobby(
    lobby: Lobby, max_queue_time_secs=120
) -> Tuple[Lobby, list[Party]]:
    """Starts lobby if it should be started.

    Also removes non-full parties if party is started because max queue time exceeded.
    """

    is_full = lobby.current_player_count() == lobby.max_players
    past_max_wait_time = lobby.queue_time >= max_queue_time_secs

    dropped_parties = []
    if is_full or past_max_wait_time:
        lobby.status = LobbyStatus.started

        for party in lobby.parties:
            if len(party) < lobby.party_size:
                lobby.parties.remove(party)
                dropped_parties.append(party)

    return lobby, dropped_parties


def maybe_cancel_matchmaking(
    lobby, max_queue_time_secs=300
) -> Tuple[Lobby, list[Party]]:
    # if past max_queue_time and no full parties
    # send parties back to menu

    past_max_wait_time = lobby.queue_time >= max_queue_time_secs
    if past_max_wait_time and lobby.status == LobbyStatus.filling:
        lobby.status = LobbyStatus.canceled
        return lobby, lobby.parties
    else:
        return lobby, []


def regroup_lobbies(
    lobbies: list[Lobby],
) -> Tuple[list[Lobby], list[Lobby], list[Lobby]]:
    "Regroups lobbies into filling, started, and canceled"

    filling = [lob for lob in lobbies if lob.status == LobbyStatus.filling]
    started = [lob for lob in lobbies if lob.status == LobbyStatus.started]
    canceled = [lob for lob in lobbies if lob.status == LobbyStatus.canceled]

    return filling, started, canceled


def matchmake_party(
    filling_lobbies: list[Lobby], party: Party, max_queue_time_secs: int = 120
) -> Tuple[list[Lobby], list[Lobby], list[Party]]:

    filling_lobbies = put_party_in_lobby(filling_lobbies, party)

    canceled_parties: list[Party] = []
    for lobby in filling_lobbies:
        _, dropped_parties = maybe_start_lobby(
            lobby, max_queue_time_secs=max_queue_time_secs
        )
        canceled_parties = canceled_parties + dropped_parties

        _, dropped_parties = maybe_cancel_matchmaking(
            lobby, max_queue_time_secs=max_queue_time_secs
        )
        canceled_parties = canceled_parties + dropped_parties

    filling_lobbies, started_lobbies, canceled_lobbies = regroup_lobbies(
        filling_lobbies
    )
    return filling_lobbies, started_lobbies, canceled_parties
