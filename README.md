# Dark and Darker Matchmaking Concept

Proof of concept for matchmaking system in Dark and Darker.

Disclaimer: This is a proof of concept for experimenation and not designed to be a drop in replacement in a production system.

## Design
Matchmaking systems have a tradeoff between three things:
1. Time players spend waiting in matchmaking queue
2. Fully populating games
3. Difference in matchmaking rating (MMR) between players in a game

### Current Constraints
* Wait time cap
* Games can be not-full. Possibly one party in a game
* Parties with MMR difference above threshold cannot be placed in same game..

### Properties
* One map at a time (currently like DaD)
* System attempts to fill non-full parties and non-full parties cannot be placed in a game (currently like DaD)
    * System will attempt to find another teammate for a duo party queued in trios but if fail to find a teammate cancel matchmaking

## Installation and Usage
1. Install [Poetry](https://python-poetry.org/docs/#installation)
2. Install requirements: `poetry install`
3. Run simulation: `poetry run python simulation.py --simulated_secs=600 --max_queue_time=300 --mmr_method=max_gs --mmr_threshold=50`
    * Current`mmr_method` are `max_gs` and `avg_gs`.
4. Open `results.json`
