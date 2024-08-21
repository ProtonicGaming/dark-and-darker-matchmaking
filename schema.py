from enum import Enum

from pydantic import BaseModel, AfterValidator, computed_field, Field

from typing import Annotated, Literal


class Job(Enum):
    bard = "bard"
    barbarian = "barbarian"
    cleric = "cleric"
    druid = "druid"
    fighter = "fighter"
    ranger = "ranger"
    rogue = "rogue"
    warlock = "warlock"
    wizard = "wizard"


class Map(Enum):
    goblin_caves = "goblin_caves"
    howing_crypts = "howling_crypts"
    ice_cavern = "ice_cavern"


class Player(BaseModel):
    job: Job
    level: int
    gear_score: int


def empty_party(p: list[Player]):
    assert len(p) > 0, "Party cannot be empty"
    return p


class Party(BaseModel):
    players: Annotated[list[Player], AfterValidator(empty_party)]
    map: Map
    # mmr: int
    max_size: int

    def __len__(self) -> int:
        return len(self.players)


class Lobby(BaseModel):
    parties: list[Party]
    map: Map

    party_size: Annotated[int, Field(ge=1, le=3)]

    @computed_field
    @property
    def max_players(self) -> int:
        match self.party_size:
            case 1:
                return 10
            case 2:
                return 14
            case 3:
                return 15

    def current_player_count(self) -> int:
        return sum([len(p) for p in self.parties])
