"""C2: hack losses over 24 months against average headline chain TVL (THESIS.md section 5, C2).

Also the descriptive tables of section 6: audits per chain, all-time losses, losses against fees.
"""
from . import config, universe
from .util import day, day_to_ts, median, read_json, usd, write_csv, write_json

D = config.RAW / "defillama"
OUT = config.DATA / "tables"


# ---------- attribution rules (pure functions, unit-tested) ----------

def plurality_chain(listing: dict):
    """The one chain holding the largest share of a listing's TVL, or None (no TVL, or a tie)."""
    tv = {k: float(v) for k, v in (listing.get("chainTvls") or {}).items()
          if "-" not in k and k not in config.NON_CHAIN_KEYS and v and float(v) > 0}
    if not tv:
        return None
    ranked = sorted(tv.items(), key=lambda kv: (-kv[1], kv[0]))
    if len(ranked) > 1 and ranked[0][1] == ranked[1][1]:
        return None
    return ranked[0][0]


def id_chain(hack: dict, by_id: dict):
    """Protocol-id route: the hack goes to the listing's largest chain, and to no other chain."""
    hid = str(hack.get("defillamaId") or "")
    if not hid.isdigit() or hid not in by_id:
        return None
    return plurality_chain(by_id[hid])


def attribute(hack: dict, chain: str, by_id: dict):
    """Return (bound, route) for this hack on this chain, or (None, None).

    bound 'lower': tagged with this chain only, or attributed by protocol id.
    bound 'upper': tagged with this chain together with others (counted in full, upper bound only).
    """
    tags = sorted({str(t).lower() for t in (hack.get("chain") or [])})
    c = chain.lower()
    routes = []
    if id_chain(hack, by_id) == chain:
        routes.append("protocol_id")
    if tags == [c]:
        routes.append("tag_single")
    if routes:
        return "lower", "+".join(routes)
    if c in tags:
        return "upper", "tag_multi"
    return None, None


def window(snapshot_date: str) -> tuple:
    end = day_to_ts(snapshot_date)
    return end - config.WINDOW_DAYS * 86400, end  # hacks and TVL points with start < t <= end (+ rest of that day)


def in_window(ts: int, start: int, end: int) -> bool:
    return start < ts <= end + 86399


def mean_tvl(history: list, start: int, end: int) -> tuple:
    pts = [float(p["tvl"]) for p in history if in_window(int(p["date"]), start, end)]
    return (sum(pts) / len(pts) if pts else None), len(pts)


def loss_rate(losses: float, mean: float) -> float:
    """Per cent of average TVL lost per year."""
    return 100.0 * losses * (365.0 / config.WINDOW_DAYS) / mean


def verdict(near: dict, peers: list) -> dict:
    """Kill criterion: fails if above the peer median on both bounds; holds if at or below on both."""
    out = {}
    for b in ("lower", "upper"):
        out[f"peer_median_{b}"] = median([p[b] for p in peers])
        out[f"near_{b}"] = near[b]
        out[f"near_above_median_{b}"] = near[b] > out[f"peer_median_{b}"]
    if out["near_above_median_lower"] and out["near_above_median_upper"]:
        out["verdict"] = "fails"
    elif not out["near_above_median_lower"] and not out["near_above_median_upper"]:
        out["verdict"] = "holds"
    else:
        out["verdict"] = "can't tell"
    return out


# ---------- tables ----------

def run() -> dict:
    protocols = read_json(D / "protocols.json.gz")
    hacks = read_json(D / "hacks.json")
    by_id = {str(p["id"]): p for p in protocols}
    snap = universe.snapshot()["snapshot_date"]
    start, end = window(snap)

    hack_rows, per_chain = [], {}
    cex_excluded = {c: 0 for c in config.CHAINS}
    for chain in config.CHAINS:
        agg = {k: 0.0 for k in ("w_lower", "w_upper", "all_lower", "all_upper", "w_returned")}
        cnt = {k: 0 for k in ("w_lower", "w_upper", "all_lower", "all_upper", "w_no_amount")}
        for h in sorted(hacks, key=lambda h: (h["date"], h["name"])):
            bound, route = attribute(h, chain, by_id)
            if bound is None:
                continue
            inw = in_window(int(h["date"]), start, end)
            if h.get("targetType") == "CEX":
                cex_excluded[chain] += 1 if inw else 0
                continue
            amt = float(h["amount"]) if h.get("amount") is not None else 0.0
            for scope, ok in (("w", inw), ("all", True)):
                if not ok:
                    continue
                agg[f"{scope}_upper"] += amt
                cnt[f"{scope}_upper"] += 1
                if bound == "lower":
                    agg[f"{scope}_lower"] += amt
                    cnt[f"{scope}_lower"] += 1
            if inw:
                agg["w_returned"] += float(h.get("returnedFunds") or 0)
                cnt["w_no_amount"] += 1 if h.get("amount") is None else 0
            hack_rows.append({
                "chain": chain, "date": day(int(h["date"])), "name": h["name"], "amount_usd": usd(h.get("amount")),
                "returned_funds_usd": usd(h.get("returnedFunds")), "bound": bound, "route": route,
                "in_24m_window": "yes" if inw else "no", "target_type": h.get("targetType"),
                "chain_tags": "|".join(h.get("chain") or []), "defillama_id": h.get("defillamaId") or "",
                "id_route_chain": id_chain(h, by_id) or "", "technique": h.get("technique") or "",
            })
        hist = read_json(D / f"chain_tvl_{chain}.json")
        mean, n_days = mean_tvl(hist, start, end)
        per_chain[chain] = {
            "chain": chain, "window_start": day(start + 86400), "window_end": snap, "tvl_days": n_days,
            "mean_headline_tvl_usd": mean, "headline_tvl_snapshot_usd": float(hist[-1]["tvl"]),
            "losses_lower_usd": agg["w_lower"], "losses_upper_usd": agg["w_upper"],
            "hacks_lower": cnt["w_lower"], "hacks_upper": cnt["w_upper"],
            "hacks_without_amount": cnt["w_no_amount"], "returned_funds_usd": agg["w_returned"],
            "cex_hacks_excluded": cex_excluded[chain],
            "loss_rate_lower_pct_per_year": loss_rate(agg["w_lower"], mean),
            "loss_rate_upper_pct_per_year": loss_rate(agg["w_upper"], mean),
            "alltime_losses_lower_usd": agg["all_lower"], "alltime_losses_upper_usd": agg["all_upper"],
            "alltime_hacks_lower": cnt["all_lower"], "alltime_hacks_upper": cnt["all_upper"],
        }

    near = {"lower": per_chain[config.NEAR]["loss_rate_lower_pct_per_year"],
            "upper": per_chain[config.NEAR]["loss_rate_upper_pct_per_year"]}
    peers = [{"lower": per_chain[c]["loss_rate_lower_pct_per_year"],
              "upper": per_chain[c]["loss_rate_upper_pct_per_year"]} for c in config.PEERS]
    v = verdict(near, peers)

    money = [k for k in per_chain[config.NEAR] if k.endswith("_usd")]
    rate_rows = []
    for c in config.CHAINS:
        r = dict(per_chain[c])
        for k in money:
            r[k] = usd(r[k])
        for k in ("loss_rate_lower_pct_per_year", "loss_rate_upper_pct_per_year"):
            r[k] = f"{r[k]:.4f}"
        rate_rows.append(r)
    write_csv(OUT / "c2_loss_rates.csv", rate_rows, list(rate_rows[0].keys()))
    write_csv(OUT / "c2_hacks_attributed.csv", hack_rows, list(hack_rows[0].keys()))
    result = {"claim": "C2", "snapshot_date": snap, "window_days": config.WINDOW_DAYS,
              **{k: (round(x, 6) if isinstance(x, float) else x) for k, x in v.items()}}
    write_json(OUT / "c2_verdict.json", result)
    return {"per_chain": per_chain, "verdict": result}


def audits() -> list:
    rows = []
    for chain in config.CHAINS:
        top = [r for r in universe.load() if r["chain"] == chain and r["in_tests"] == "yes"]
        audited = [r for r in top if (r["audits_flag"] not in ("0", "", "None")) or r["audit_links"] > 0]
        tvl = sum(r["listing_tvl_usd"] for r in top)
        rows.append({
            "chain": chain, "listings": len(top), "with_audit_flag_or_link": len(audited),
            "share_by_count_pct": f"{100 * len(audited) / len(top):.1f}",
            "share_by_listing_tvl_pct": f"{100 * sum(r['listing_tvl_usd'] for r in audited) / tvl:.1f}",
            "mean_audit_links": f"{sum(r['audit_links'] for r in top) / len(top):.2f}",
            "listings_with_zero_links": sum(1 for r in top if r["audit_links"] == 0),
        })
    write_csv(OUT / "audits_by_chain.csv", rows, list(rows[0].keys()))
    return rows


def losses_vs_fees() -> list:
    """Per NEAR listing in the tests: hack losses by protocol id against fees, over the clipped window."""
    hacks = read_json(D / "hacks.json")
    snap = universe.snapshot()["snapshot_date"]
    start, end = window(snap)
    rows = []
    for r in universe.load():
        if r["chain"] != config.NEAR or r["in_tests"] != "yes":
            continue
        f = read_json(D / "fees" / f"{r['slug']}.json")
        chart = f.get("totalDataChart") or []
        mine = [h for h in hacks if str(h.get("defillamaId") or "") == str(r["defillama_id"])]
        row = {"protocol": r["protocol"], "slug": r["slug"], "fee_data": "yes" if chart else "no"}
        in24 = [h for h in mine if in_window(int(h["date"]), start, end)]
        row["hack_losses_24m_usd"] = usd(sum(float(h.get("amount") or 0) for h in in24))
        if chart:
            first = int(chart[0][0])
            cs = max(start, first - 1)  # clip the window to the first day of fee data
            fees = sum(float(v or 0) for t, v in chart if in_window(int(t), cs, end))
            losses = sum(float(h.get("amount") or 0) for h in mine if in_window(int(h["date"]), cs, end))
            row.update({
                "fee_window_start": day(max(start + 86400, first)), "fee_window_end": snap,
                "fees_usd": usd(fees), "hack_losses_in_fee_window_usd": usd(losses),
                "losses_over_fees": f"{losses / fees:.4f}" if fees > 0 else "",
                "fee_chains": "|".join(f.get("chains") or []),
            })
        rows.append(row)
    cols = ["protocol", "slug", "fee_data", "fee_window_start", "fee_window_end", "fees_usd",
            "hack_losses_in_fee_window_usd", "losses_over_fees", "hack_losses_24m_usd", "fee_chains"]
    write_csv(OUT / "near_losses_vs_fees.csv", rows, cols)
    return rows
