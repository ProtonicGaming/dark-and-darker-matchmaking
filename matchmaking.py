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


MMR_FUNCTIONS = {"max_gs": max_gearscore_mmr, "avg_gs": average_gearscore_mmr}


def are_parties_matchable(
    party_a: Party, party_b: Party, mmr_fn=max_gearscore_mmr, mmr_threshold=50
) -> bool:
    "Decides if parties are matchable if mmr is within 'threshold'"

    a_mmr = mmr_fn(party_a)
    b_mmr = mmr_fn(party_b)
    can_match = abs(a_mmr - b_mmr) <= mmr_threshold

    return can_match


def can_add_party_to_lobby(
    lobby: Lobby, party: Party, mmr_method="max_gs", mmr_threshold=50
) -> bool:
    """Determines if party can be added to lobby.

    Every party in the lobby must be matchable with new potential party"""

    try:
        mmr_fn = MMR_FUNCTIONS[mmr_method]
    except KeyError:
        raise NotImplementedError(f"No implementation for mmr method: {mmr_method}")

    for lobby_party in lobby.parties:
        if not are_parties_matchable(
            lobby_party, party, mmr_fn=mmr_fn, mmr_threshold=mmr_threshold
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
    lobby: Lobby, party: Party, mmr_method="max_gs", mmr_threshold=50, **kwargs
) -> tuple[bool, Party]:
    # mmr check
    mmr_check = can_add_party_to_lobby(
        lobby, party, mmr_method=mmr_method, mmr_threshold=mmr_threshold
    )
    # Will adding party to lobby go over lobby max players?
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


def put_party_in_lobby(
    filling_lobbies: list[Lobby], party: Party, **kwargs
) -> list[Lobby]:
    """Adds a party from the matchmaking queue to lobbies being filled."""

    # No existing lobbies: create one
    if not filling_lobbies:
        new_lobby = Lobby(parties=[party], map=party.map, party_size=party.max_size)
        filling_lobbies.append(new_lobby)
    else:
        successfully_added_party = False
        for lobby in filling_lobbies:
            # attempt to add to existing lobbies
            was_merged, _ = attempt_add_party_to_lobby(lobby, party, **kwargs)
            if was_merged:
                successfully_added_party = True
                break
        # No matchable lobbies: create new lobby
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

    # only full if sum of full parties is max lobby player count
    num_players_in_full_parties = sum(
        len(p) for p in lobby.parties if len(p) == lobby.party_size
    )

    is_full = num_players_in_full_parties == lobby.max_players
    past_max_wait_time = lobby.queue_time >= max_queue_time_secs

    dropped_parties = []
    if is_full or past_max_wait_time:


        for party in lobby.parties:
            if len(party) < lobby.party_size:
                lobby.parties.remove(party)
                dropped_parties.append(party)

        # no full parties, cancel lobby
        # since we removed non-full parties lobby will be empty
        if num_players_in_full_parties == 0:
            lobby.status = LobbyStatus.canceled
        else:
            lobby.status = LobbyStatus.started

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
