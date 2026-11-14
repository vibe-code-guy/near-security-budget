"""Write site/data.js: everything the static dashboard shows, taken from the built tables.

The dashboard is opened from disk (file://), where fetch() of JSON is blocked, so the data
is a script that sets one global. No network, no build step.
"""
import json

from . import config, universe
from .util import read_csv, read_json

T = config.DATA / "tables"


def opt_json(name: str):
    p = T / name
    return read_json(p) if p.exists() else None


def opt_csv(name: str):
    p = T / name
    return read_csv(p) if p.exists() else None


def run() -> None:
    manifest = read_json(config.RAW / "manifest.json")["files"]
    snap = universe.snapshot()
    near_heights = [v["block_height"] for k, v in manifest.items() if k.startswith("data/raw/near/") and v.get("block_height")]
    data = {
        "snapshot": snap,
        "retrieval": {
            "defillama_first_pull": manifest["data/raw/defillama/protocols.json.gz"]["retrieved_at"],
            "near_view_calls": max(v["retrieved_at"] for k, v in manifest.items() if k.startswith("data/raw/near/")),
            "near_block_min": min(near_heights), "near_block_max": max(near_heights),
            "near_rpc": config.NEAR_RPC,
        },
        "registration": {
            "commit": "f84b54871db3b51f5db5ff113b34ef0f76745f56",
            "sha256": "2b99cec36f2b2d575367d2e053d006a3495df0fcbffc0294b52dd77ff921b58b",
            "committed_utc": "2026-11-13 06:45:58", "ots_stamp_utc": "2026-11-13 07:27",
            "ots_bitcoin_blocks": [975645, 975648, 975658],
            "anchor_utc": "2026-11-13 11:41:07", "anchor_account": "near-thesis.near",
            "anchor_tx": "DsdB2BqHAHxyY2Ud4GYcek7JirLYMJz2tLY1iDNAVXji", "anchor_block": 224358450,
        },
        "universe": universe.load(),
        "c1": opt_json("c1_verdict.json"), "c1_rows": opt_csv("c1_protocols.csv"),
        "c1_bands": opt_csv("c1_bands.csv"), "c1_coverage": opt_csv("c1_coverage.csv"),
        "c1_sensitivity": opt_json("c1_sensitivity.json"),
        "c2": opt_json("c2_verdict.json"), "c2_rates": opt_csv("c2_loss_rates.csv"),
        "c2_hacks": [r for r in (opt_csv("c2_hacks_attributed.csv") or []) if r["in_24m_window"] == "yes"],
        "c2_sensitivity": opt_json("c2_sensitivity.json"), "c2_sensitivity_rows": opt_csv("c2_sensitivity.csv"),
        "c3": opt_json("c3_verdict.json"), "c3_rows": opt_csv("c3_control.csv"), "c3_daos": opt_csv("c3_daos.csv"),
        "audits": opt_csv("audits_by_chain.csv"), "fees": opt_csv("near_losses_vs_fees.csv"),
        "timeline": opt_csv("timeline.csv"), "timeline_derived": opt_json("timeline_derived.json"),
    }
    config.SITE.mkdir(exist_ok=True)
    body = "window.DATA = " + json.dumps(data, indent=1, sort_keys=True, ensure_ascii=True) + ";\n"
    (config.SITE / "data.js").write_bytes(body.encode("utf-8"))
    print("site/data.js written")
