# Dark and Darker Matchmaking Concept

Proof of concept for matchmaking system in Dark and Darker

## Design
Matchmaking systems have a tradeoff between three things:
1. Time players spend waiting in matchmaking queue
2. Fully populating games
3. Difference in matchmaking rating (MMR) between players in a game

### Current Constraints
* Wait time cap
* Games can be not-full. Possibly one party in a game
* Max MMR difference between parties to be placed in the same game.

### Properties
* Game map rotates (currently like DaD)
* System attempts to fill parties and incomplete parties cannot be placed in a game (currently like DaD)
    * System will attempt to find another teammate for a duo party queued in trios but if fail to find a teammate cancel matchmaking
