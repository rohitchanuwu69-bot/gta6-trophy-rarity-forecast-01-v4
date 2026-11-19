"""Week-one earn-rate forecasts for GTA VI trophies on PS5.

One forecast file is produced for every case file found in the
input folder, five quantiles per trophy in each file."""

import os, math, json, glob
from datetime import timezone as utc, datetime as stamp


TITLES = (0.05, 0.25, 0.5, 0.75, 0.95)
JUMP = 3868.0 / 638.0
ROOKIE = 0.30
NARROW = 0.14
WIDE_TOP = 0.30
WIDEST = 0.55
LAUNCH = stamp(2026, 11, 19, tzinfo=utc.utc)


def read_stamp(text):
    return stamp.fromisoformat(text.replace("Z", "+00:00"))


def age_minutes(moment):
    gap = (moment - LAUNCH).total_seconds() / 60.0
    return gap if gap > 1.0 else 1.0


def odds(pct):
    frac = sorted((1e-5, pct / 100.0, 1.0 - 1e-5))[1]
    return math.log(frac) - math.log(1.0 - frac)


def squash(x):
    return 1.0 / (1.0 + math.exp(-x)) if x >= 0.0 else math.exp(x) / (1.0 + math.exp(x))


def quantiles(mid_pct, low_half, high_half):
    middle = odds(mid_pct)
    steps = (-low_half, -low_half / 2.0, 0.0, high_half / 2.0, high_half)
    vals = [squash(middle + step) * 100.0 for step in steps]
    picked = []
    floor = 0.0
    for val in vals:
        num = round(val, 2)
        num = 0.0 if num < 0.0 else (100.0 if num > 100.0 else num)
        num = floor if num < floor else num
        picked.append(num)
        floor = num
    return picked


def straight(xs, ys):
    count = len(xs)
    mx = sum(xs) / count
    my = sum(ys) / count
    spread_x = sum((x - mx) ** 2 for x in xs)
    if spread_x <= 0.0:
        return my, 0.0
    cross = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    slope = cross / spread_x
    return my - slope * mx, slope


def frozen_case(case):
    snaps = case["history"]
    final = snaps[-1]
    tracked = float(final["players_tracked"])
    aimed = tracked * JUMP
    shares = [float(v) for v in final["rates"]]
    got = [round(s / 100.0 * tracked) for s in shares]
    ranking = sorted((k for k, s in enumerate(shares) if s < 99.995),
        key=lambda k: (-shares[k], case["trophies"][k]["id"]))
    quick = set(ranking[:3])
    table = []
    for k, prize in enumerate(case["trophies"]):
        share = shares[k]
        top = WIDE_TOP if k in quick else NARROW
        extra = ROOKIE * (share / 100.0) * (aimed - tracked) if k in quick else 0.0
        mid = 100.0 * (got[k] + extra) / aimed
        qs = [100.0, 100.0, 100.0, 100.0, 100.0] if share >= 99.995 else quantiles(mid, NARROW, top)
        table.append({"id": prize["id"], "q": qs})
    return table


def trending_case(case):
    snaps = case["history"]
    moments = [math.log(age_minutes(read_stamp(s["at"]))) for s in snaps]
    tracked = [float(s["players_tracked"]) for s in snaps]
    log_tracked = [math.log(p) if p > 0 else 0.0 for p in tracked]
    p0, p1 = straight(moments, log_tracked)
    aim_moment = math.log(age_minutes(read_stamp(case["target"])))
    aim_tracked = math.exp(p0 + p1 * aim_moment)
    hours = max(0.0, float(case.get("horizon_minutes", 90)) / 60.0)
    table = []
    for k, prize in enumerate(case["trophies"]):
        recent = float(snaps[-1]["rates"][k])
        if recent >= 99.995:
            table.append({"id": prize["id"], "q": [100.0, 100.0, 100.0, 100.0, 100.0]})
        if recent < 99.995:
            log_got = []
            used = []
            for j, snap in enumerate(snaps):
                num = round(float(snap["rates"][k]) / 100.0 * float(snap["players_tracked"]))
                if num > 0:
                    log_got.append(math.log(num))
                    used.append(moments[j])
            if len(used) < 2:
                cold = max(0.0, round(recent / 100.0 * tracked[-1]))
                mid = 100.0 * cold / max(aim_tracked, 1.0)
                table.append({"id": prize["id"], "q": quantiles(mid, WIDEST, WIDEST)})
            if len(used) >= 2:
                e0, e1 = straight(used, log_got)
                fitted = [e0 + e1 * t for t in used]
                resid = [y - f for y, f in zip(log_got, fitted)]
                jitter = math.sqrt(sum(r * r for r in resid) / len(resid))
                aim_got = math.exp(e0 + e1 * aim_moment)
                mid = 100.0 * aim_got / max(aim_tracked, 1.0)
                mid = 0.0 if mid < 0.0 else (100.0 if mid > 100.0 else mid)
                half = min(WIDEST, NARROW + jitter + 0.02 * hours)
                table.append({"id": prize["id"], "q": quantiles(mid, half, half)})
    return table


def predict_case(case):
    snaps = case.get("history") or []
    if not snaps:
        return [{"id": t["id"], "q": quantiles(1.0, WIDEST, WIDEST)} for t in case["trophies"]]
    first = snaps[0]
    same = all(s["players_tracked"] == first["players_tracked"] and s["rates"] == first["rates"] for s in snaps)
    return frozen_case(case) if same else trending_case(case)


def forecast_all():
    src = os.environ.get("MAKEFUN_INPUT_DIR", "/input")
    dst = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(dst, exist_ok=True)
    for path in sorted(glob.glob(os.path.join(src, "*.in"))):
        with open(path, "r", encoding="utf-8") as fp:
            case = json.load(fp)
        grid = predict_case(case)
        name = os.path.splitext(os.path.basename(path))[0]
        dest = os.path.join(dst, name + ".out")
        with open(dest, "w", encoding="utf-8") as fp:
            json.dump({"trophies": grid}, fp, separators=(",", ":"))
            fp.write("\n")


forecast_all()
