"""C1: bug bounty coverage and size-matched bounty-to-TVL ratio (THESIS.md section 5, C1).

Input: data/bounties.csv, filled by hand from the public programme pages. Until every row
has a status, nothing is computed and no C1 output exists.
"""
from . import config, universe
from .util import median, read_csv, usd, write_csv, write_json

OUT = config.DATA / "tables"
FILES = ["c1_protocols.csv", "c1_bands.csv", "c1_coverage.csv", "c1_verdict.json"]
STATUSES = {"live", "none_found", "undetermined"}


# ---------- pure rules (unit-tested) ----------

def num(x):
    x = str(x or "").replace(",", "").replace("$", "").replace("%", "").strip()
    return float(x) if x else None


def effective_max(status: str, cap, pct, total_tvl: float) -> tuple:
    """(effective maximum in USD or None, status after the rule, derived flag).

    Fixed maximum -> that figure. Tied to funds at risk with a cap -> min(cap, pct x total TVL).
    Percentage with no cap -> pct x total TVL. Live but no USD figure readable -> undetermined.
    """
    if status == "none_found":
        return 0.0, status, False
    if status == "undetermined":
        return None, status, False
    if cap is None and pct is None:
        return None, "undetermined", False
    if pct is None:
        return cap, status, False
    leg = pct / 100.0 * total_tvl
    if cap is None or leg < cap:
        return leg, status, True
    return cap, status, False


def band_of(total_tvl: float) -> int:
    for i, (_, lo, hi) in enumerate(config.BANDS):
        if lo <= total_tvl < hi:
            return i
    return len(config.BANDS) - 1


def merge_bands(peer_counts: list) -> list:
    """Groups of band indexes. A group with fewer than 3 peers merges into the group below it
    (the lowest merges into the one above), repeated until every group has at least 3."""
    groups = [[i] for i in range(len(peer_counts))]
    count = lambda g: sum(peer_counts[i] for i in g)
    while len(groups) > 1:
        small = next((k for k, g in enumerate(groups) if count(g) < config.MIN_PEERS_PER_BAND), None)
        if small is None:
            break
        if small == 0:
            groups[0:2] = [groups[0] + groups[1]]
        else:
            groups[small - 1:small + 1] = [groups[small - 1] + groups[small]]
    return groups


def band_label(group: list) -> str:
    lo, hi = config.BANDS[group[0]][1], config.BANDS[group[-1]][2]
    f = lambda v: "$%gB" % (v / 1e9) if v >= 1e9 else "$%gM" % (v / 1e6)
    return f"under {f(hi)}" if lo == 0 else (f"over {f(lo)}" if hi == float("inf") else f"{f(lo)} to {f(hi)}")


def claim_verdict(coverage: dict, undetermined: dict, near_score: float) -> dict:
    peer_cov = median([coverage[c] for c in config.PEERS])
    c1a = "fails" if coverage[config.NEAR] < peer_cov - 10.0 else "holds"
    c1b = "fails" if near_score < 50.0 else "holds"
    cant = undetermined[config.NEAR] > 20.0 or sum(1 for c in config.PEERS if undetermined[c] > 20.0) >= 2
    verdict = "can't tell" if cant else ("fails" if "fails" in (c1a, c1b) else "holds")
    return {"c1a": c1a, "c1b": c1b, "verdict": verdict, "peer_median_coverage_pct": round(peer_cov, 2),
            "near_coverage_pct": round(coverage[config.NEAR], 2), "near_score_pct": round(near_score, 2)}


# ---------- tables ----------

def clear() -> None:
    for f in FILES:
        (OUT / f).unlink(missing_ok=True)


def run():
    if not universe.BOUNTIES_CSV.exists():
        clear()
        return None
    filled = read_csv(universe.BOUNTIES_CSV)
    blank = [r["slug"] for r in filled if not (r.get("status") or "").strip()]
    if blank:
        clear()
        print(f"C1: not computed, data/bounties.csv has {len(blank)} of {len(filled)} rows without a status")
        return None
    by_key = {(r["chain"], r["slug"]): r for r in filled}
    rows = []
    for u in universe.load():
        b = by_key[(u["chain"], u["slug"])]
        status = b["status"].strip().lower()
        assert status in STATUSES, f"{u['slug']}: status {status!r} is not one of {sorted(STATUSES)}"
        eff, status2, derived = effective_max(status, num(b.get("max_critical_usd")), num(b.get("funds_at_risk_pct")), u["total_tvl_usd"])
        rows.append({**u, "status": status2, "status_entered": status, "effective_max": eff, "derived": derived,
                     "ratio": None if eff is None else eff / u["total_tvl_usd"], "band": band_of(u["total_tvl_usd"]),
                     "platform": b.get("platform", ""), "url": b.get("url", ""), "cap_rule": b.get("cap_rule", ""),
                     "max_critical_usd": b.get("max_critical_usd", ""), "funds_at_risk_pct": b.get("funds_at_risk_pct", ""),
                     "payout_token": b.get("payout_token", ""), "vesting": b.get("vesting", ""),
                     "checked_sources": b.get("checked_sources", ""), "retrieved_at": b.get("retrieved_at", ""),
                     "notes": b.get("notes", "")})

    peers = [r for r in rows if r["chain"] != config.NEAR and r["status"] != "undetermined"]
    groups = merge_bands([sum(1 for r in peers if r["band"] == i) for i in range(len(config.BANDS))])
    group_of = {i: k for k, g in enumerate(groups) for i in g}
    bars = {k: median([r["ratio"] for r in peers if group_of[r["band"]] == k]) for k in range(len(groups))}
    near = [r for r in rows if r["chain"] == config.NEAR and r["in_tests"] == "yes"]
    for r in rows:
        k = group_of[r["band"]]
        r["band_label"], r["bar"] = band_label(groups[k]), bars[k]
        r["meets"] = r["ratio"] is not None and bars[k] is not None and r["ratio"] >= bars[k]
    near_tvl = sum(r["listing_tvl_usd"] for r in near)
    score = 100.0 * sum(r["listing_tvl_usd"] for r in near if r["meets"]) / near_tvl
    zero_bar = [r["protocol"] for r in near if r["meets"] and r["bar"] == 0 and r["ratio"] == 0]

    coverage, undet, cov_rows = {}, {}, []
    for chain in config.CHAINS:
        top = [r for r in rows if r["chain"] == chain and r["in_tests"] == "yes"]
        tvl = sum(r["listing_tvl_usd"] for r in top)
        coverage[chain] = 100.0 * sum(r["listing_tvl_usd"] for r in top if r["status"] == "live") / tvl
        undet[chain] = 100.0 * sum(r["listing_tvl_usd"] for r in top if r["status"] == "undetermined") / tvl
        cov_rows.append({"chain": chain, "top10_tvl_usd": usd(tvl), "coverage_pct": f"{coverage[chain]:.2f}",
                         "undetermined_pct": f"{undet[chain]:.2f}",
                         "live": sum(1 for r in top if r["status"] == "live"),
                         "none_found": sum(1 for r in top if r["status"] == "none_found"),
                         "undetermined": sum(1 for r in top if r["status"] == "undetermined")})
    v = claim_verdict(coverage, undet, score)
    v.update({"claim": "C1", "near_zero_bar_cases": zero_bar,
              "near_undetermined_pct": round(undet[config.NEAR], 2),
              "peer_chains_over_20pct_undetermined": [c for c in config.PEERS if undet[c] > 20.0]})

    band_rows = []
    for k, g in enumerate(groups):
        mine = [r for r in near if group_of[r["band"]] == k]
        band_rows.append({"band": band_label(g), "peers": sum(1 for r in peers if group_of[r["band"]] == k),
                          "peer_bar_pct": "" if bars[k] is None else f"{100 * bars[k]:.4f}",
                          "near_at_or_above": ", ".join(r["protocol"] for r in mine if r["meets"]),
                          "near_below": ", ".join(r["protocol"] for r in mine if not r["meets"])})
    out = [{"chain": r["chain"], "rank": r["rank"], "in_tests": r["in_tests"], "protocol": r["protocol"], "slug": r["slug"],
            "listing_tvl_usd": usd(r["listing_tvl_usd"]), "total_tvl_usd": usd(r["total_tvl_usd"]), "status": r["status"],
            "max_critical_usd": r["max_critical_usd"], "funds_at_risk_pct": r["funds_at_risk_pct"],
            "effective_max_usd": usd(r["effective_max"]), "derived": "yes" if r["derived"] else "no",
            "ratio_pct": "" if r["ratio"] is None else f"{100 * r['ratio']:.4f}", "band": r["band_label"],
            "peer_bar_pct": "" if r["bar"] is None else f"{100 * r['bar']:.4f}",
            "at_or_above_bar": "yes" if r["meets"] else "no", "platform": r["platform"], "url": r["url"],
            "cap_rule": r["cap_rule"], "payout_token": r["payout_token"], "vesting": r["vesting"],
            "checked_sources": r["checked_sources"], "retrieved_at": r["retrieved_at"], "notes": r["notes"]} for r in rows]
    write_csv(OUT / "c1_protocols.csv", out, list(out[0].keys()))
    write_csv(OUT / "c1_bands.csv", band_rows, list(band_rows[0].keys()))
    write_csv(OUT / "c1_coverage.csv", cov_rows, list(cov_rows[0].keys()))
    write_json(OUT / "c1_verdict.json", v)
    print("C1a:", v["c1a"], "| C1b:", v["c1b"], "| C1:", v["verdict"],
          f"| coverage NEAR {v['near_coverage_pct']}% vs peer median {v['peer_median_coverage_pct']}% | score {v['near_score_pct']}%")
    return v
