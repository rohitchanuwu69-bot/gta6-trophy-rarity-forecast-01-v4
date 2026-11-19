#!/usr/bin/env python3
"""Trophy Dilution Forecaster v4: week-one GTA VI trophy earn rates.

Reads every case file in the input directory and writes one forecast
file per case to the output directory.
"""

import glob
import json
import math
import os
from datetime import datetime, timezone

QUANTILES = (0.05, 0.25, 0.5, 0.75, 0.95)
GROWTH = 3868.0 / 638.0
NEWCOMER_RATE = 0.30
HALF_BAND = 0.14
FAST_UPPER = 0.30
MAX_HALF_BAND = 0.55
RELEASE_AT = datetime(2026, 11, 19, tzinfo=timezone.utc)


def parse_time(text):
    return datetime.fromisoformat(text.replace("Z", "+00:00"))


def minutes_since_release(moment):
    delta = (moment - RELEASE_AT).total_seconds() / 60.0
    return delta if delta > 1.0 else 1.0


def logit(p):
    p = min(max(p, 1e-5), 1.0 - 1e-5)
    return math.log(p / (1.0 - p))


def sigmoid(x):
    if x >= 0.0:
        return 1.0 / (1.0 + math.exp(-x))
    top = math.exp(x)
    return top / (1.0 + top)


def band(median_pct, lower_half, upper_half):
    centre = logit(median_pct / 100.0)
    raw = (
        sigmoid(centre - lower_half) * 100.0,
        sigmoid(centre - lower_half / 2.0) * 100.0,
        sigmoid(centre) * 100.0,
        sigmoid(centre + upper_half / 2.0) * 100.0,
        sigmoid(centre + upper_half) * 100.0,
    )
    out = []
    last = 0.0
    for value in raw:
        clipped = min(max(round(value, 2), 0.0), 100.0)
        if clipped < last:
            clipped = last
        out.append(clipped)
        last = clipped
    return out


def least_squares(xs, ys):
    n = len(xs)
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    sxx = sum((x - mean_x) ** 2 for x in xs)
    if sxx <= 0.0:
        return mean_y, 0.0
    sxy = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    slope = sxy / sxx
    return mean_y - slope * mean_x, slope


def flat_forecast(case):
    reads = case["history"]
    last = reads[-1]
    players = float(last["players_tracked"])
    target_players = players * GROWTH
    rates = [float(v) for v in last["rates"]]
    earned = [round(r / 100.0 * players) for r in rates]
    order = sorted(
        (i for i, r in enumerate(rates) if r < 99.995),
        key=lambda i: (-rates[i], case["trophies"][i]["id"]),
    )
    fast = set(order[:3])
    rows = []
    for i, trophy in enumerate(case["trophies"]):
        rate = rates[i]
        if rate >= 99.995:
            rows.append({"id": trophy["id"], "q": [100.0, 100.0, 100.0, 100.0, 100.0]})
            continue
        if i in fast:
            extra = NEWCOMER_RATE * (rate / 100.0) * (target_players - players)
            median = 100.0 * (earned[i] + extra) / target_players
            rows.append({"id": trophy["id"], "q": band(median, HALF_BAND, FAST_UPPER)})
        else:
            median = 100.0 * earned[i] / target_players
            rows.append({"id": trophy["id"], "q": band(median, HALF_BAND, HALF_BAND)})
    return rows


def moving_forecast(case):
    reads = case["history"]
    times = [math.log(minutes_since_release(parse_time(r["at"]))) for r in reads]
    players = [float(r["players_tracked"]) for r in reads]
    log_players = [math.log(p) if p > 0 else 0.0 for p in players]
    p_intercept, p_slope = least_squares(times, log_players)
    target_time = math.log(minutes_since_release(parse_time(case["target"])))
    players_target = math.exp(p_intercept + p_slope * target_time)
    horizon_hours = max(0.0, float(case.get("horizon_minutes", 90)) / 60.0)
    rows = []
    for i, trophy in enumerate(case["trophies"]):
        last_rate = float(reads[-1]["rates"][i])
        if last_rate >= 99.995:
            rows.append({"id": trophy["id"], "q": [100.0, 100.0, 100.0, 100.0, 100.0]})
            continue
        earned_logs = []
        used_times = []
        for j, read in enumerate(reads):
            count = round(float(read["rates"][i]) / 100.0 * float(read["players_tracked"]))
            if count > 0:
                earned_logs.append(math.log(count))
                used_times.append(times[j])
        if len(used_times) < 2:
            frozen = max(0.0, round(last_rate / 100.0 * players[-1]))
            median = 100.0 * frozen / max(players_target, 1.0)
            rows.append({"id": trophy["id"], "q": band(median, MAX_HALF_BAND, MAX_HALF_BAND)})
            continue
        e_intercept, e_slope = least_squares(used_times, earned_logs)
        fitted = [e_intercept + e_slope * t for t in used_times]
        resid = [y - f for y, f in zip(earned_logs, fitted)]
        spread = math.sqrt(sum(r * r for r in resid) / len(resid))
        earned_target = math.exp(e_intercept + e_slope * target_time)
        median = 100.0 * earned_target / max(players_target, 1.0)
        median = min(max(median, 0.0), 100.0)
        half = min(MAX_HALF_BAND, HALF_BAND + spread + 0.02 * horizon_hours)
        rows.append({"id": trophy["id"], "q": band(median, half, half)})
    return rows


def forecast(case):
    reads = case.get("history") or []
    if not reads:
        return [
            {"id": t["id"], "q": band(1.0, MAX_HALF_BAND, MAX_HALF_BAND)}
            for t in case["trophies"]
        ]
    first = reads[0]
    flat = all(
        r["players_tracked"] == first["players_tracked"] and r["rates"] == first["rates"]
        for r in reads
    )
    if flat:
        return flat_forecast(case)
    return moving_forecast(case)


def main():
    in_dir = os.environ.get("MAKEFUN_INPUT_DIR") or "/input"
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    os.makedirs(out_dir, exist_ok=True)
    for path in sorted(glob.glob(os.path.join(in_dir, "*.in"))):
        with open(path, "r", encoding="utf-8") as handle:
            case = json.load(handle)
        rows = forecast(case)
        stem = os.path.splitext(os.path.basename(path))[0]
        out_path = os.path.join(out_dir, stem + ".out")
        with open(out_path, "w", encoding="utf-8") as handle:
            json.dump({"trophies": rows}, handle, separators=(",", ":"))
            handle.write("\n")


if __name__ == "__main__":
    main()
