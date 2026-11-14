"""Case study timeline (THESIS.md section 6): every row carries its source.

Chain rows take time, method, caller and receiver from the cached explorer responses;
only the description is written by hand (data/timeline_events.json).
"""
from datetime import datetime, timezone

from . import config
from .util import read_json, write_csv, write_json

EVENTS = config.DATA / "timeline_events.json"
RAW = config.RAW / "nearblocks"
OUT = config.DATA / "tables"


def ts(ns: str) -> str:
    return datetime.fromtimestamp(int(ns) / 1e9, timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def chain_row(event: dict) -> dict:
    rows = [t for t in read_json(RAW / event["file"])["txns"]
            if t["transaction_hash"] == event["tx"] and t["receiver_account_id"] == event["receiver"]]
    assert rows, f"transaction {event['tx']} not in {event['file']}"
    t = rows[-1]
    ok = (t.get("outcomes") or {}).get("status")
    assert ok is True, f"transaction {event['tx']} did not succeed"
    methods = [a.get("method") or a.get("action") for a in (t.get("actions") or [])]
    return {"time_utc": ts(t["block_timestamp"]), "precision": "second", "source": "chain",
            "caller": t["predecessor_account_id"], "receiver": t["receiver_account_id"],
            "method": " + ".join(m for m in methods if m), "tx": event["tx"]}


def seconds(a: str, b: str) -> int:
    f = lambda s: datetime.strptime(s if len(s) > 16 else s + ":00", "%Y-%m-%d %H:%M:%S")
    return int((f(b) - f(a)).total_seconds())


def run() -> dict:
    spec = read_json(EVENTS)
    rows = []
    for e in spec["events"]:
        if "tx" in e:
            r = chain_row(e)
            r["source_url"] = spec["sources"]["chain"]["url"] + e["tx"]
        else:
            r = {"time_utc": e["time"], "precision": e["precision"], "source": e["source"],
                 "caller": "", "receiver": "", "method": "", "tx": "",
                 "source_url": spec["sources"][e["source"]]["url"]}
        r["what"] = e["what"]
        rows.append(r)
    rows.sort(key=lambda r: (r["time_utc"][:10], r["time_utc"] if r["precision"] != "day" else r["time_utc"] + " 12:00"))
    by_tx = {r["tx"][:8]: r for r in rows if r["tx"]}
    detected = "2026-10-01 08:04"
    first_w, last_w = "2026-09-29 16:14", "2026-10-01 05:54"
    pause, fix, release = by_tx["GXpc6rSv"]["time_utc"], by_tx["FPLaCtdy"]["time_utc"], by_tx["44S4bXMi"]["time_utc"]
    derived = {
        "first_withdrawal_to_detection_minutes": seconds(first_w, detected) // 60,
        "detection_to_pause_minutes": seconds(detected, pause) // 60,
        "detection_to_fix_deployed_minutes": seconds(detected, fix) // 60,
        "pause_to_fix_minutes": seconds(pause, fix) // 60,
        "last_withdrawal_to_detection_minutes": seconds(last_w, detected) // 60,
        "dao_release_registration_to_mainnet_upgrade_minutes": seconds(release, fix) // 60,
        "pause_caller": by_tx["GXpc6rSv"]["caller"], "fix_caller": by_tx["FPLaCtdy"]["caller"],
        "inputs": {"detected": detected + " (postmortem)", "first_withdrawal": first_w + " (postmortem)",
                   "last_withdrawal": last_w + " (postmortem)", "pause": pause + " (chain)", "fix": fix + " (chain)", "release_registered": release + " (chain)"},
        "sources": spec["sources"],
    }
    write_csv(OUT / "timeline.csv", rows, ["time_utc", "precision", "source", "what", "caller", "receiver", "method", "tx", "source_url"])
    write_json(OUT / "timeline_derived.json", derived)
    return {"rows": rows, "derived": derived}
