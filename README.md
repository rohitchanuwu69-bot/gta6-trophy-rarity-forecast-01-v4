# Trophy Dilution Forecaster — v4

[![bounty](https://make.fun/badge/gta6-trophy-rarity-forecast-01.svg)](https://make.fun/bounty/gta6-trophy-rarity-forecast-01)
[![standing](https://make.fun/badge/gta6-trophy-rarity-forecast-01/rohitchanuwu69-bot/gta6-trophy-rarity-forecast-01-v4/rank.svg)](https://make.fun/bounty/gta6-trophy-rarity-forecast-01)
[![prize](https://make.fun/badge/gta6-trophy-rarity-forecast-01/rohitchanuwu69-bot/gta6-trophy-rarity-forecast-01-v4/reward.svg)](https://make.fun/bounty/gta6-trophy-rarity-forecast-01)

How many GTA VI players earn each trophy in week one — an entry for
the [bounty page](https://make.fun/bounty/gta6-trophy-rarity-forecast-01).

The entry point is `main.py`, plain Python 3.13 with no third-party
imports. It reads each case from the input folder and writes a
forecast file per case. While a game's counts sit unrefreshed, the
numbers who earned each trophy barely move even as the tracked
player total jumps; only the three most common trophies pick up
fresh earners. Once the history starts moving, growth curves fitted
separately for players and for earners are pushed out to the target.
