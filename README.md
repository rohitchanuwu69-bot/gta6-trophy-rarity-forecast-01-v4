# Trophy Dilution Forecaster v4

[![make.fun bounty](https://make.fun/badge/gta6-trophy-rarity-forecast-01.svg)](https://make.fun/bounty/gta6-trophy-rarity-forecast-01)
[![rank](https://make.fun/badge/gta6-trophy-rarity-forecast-01/rohitchanuwu69-bot/gta6-trophy-rarity-forecast-01-v4/rank.svg)](https://make.fun/bounty/gta6-trophy-rarity-forecast-01)
[![reward](https://make.fun/badge/gta6-trophy-rarity-forecast-01/rohitchanuwu69-bot/gta6-trophy-rarity-forecast-01-v4/reward.svg)](https://make.fun/bounty/gta6-trophy-rarity-forecast-01)

Forecasts how many GTA VI players earn each trophy in week one, for the
[make.fun bounty](https://make.fun/bounty/gta6-trophy-rarity-forecast-01).

`main.py` (Python 3.13, standard library only) reads every case in the
input directory and writes one forecast per case. While Exophase has not
refreshed a game's counts, earned counts stay frozen as the tracked
player count jumps; only the three commonest trophies gain new earners.
When the history moves, separate growth fits for players and earned
counts are extrapolated to the target.
