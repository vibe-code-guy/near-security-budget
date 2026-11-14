"""`make all` minus the tests: rebuild every table from the cached raw data. No network."""
from . import c2


def main() -> None:
    res = c2.run()
    print("C2:", res["verdict"]["verdict"], "| NEAR lower/upper %/yr:",
          res["verdict"]["near_lower"], res["verdict"]["near_upper"],
          "| peer median:", res["verdict"]["peer_median_lower"], res["verdict"]["peer_median_upper"])
    sens = c2.sensitivity(res["per_chain"])
    print("C2 sensitivity (not registered), same rule on the wider base:", sens["same_rule_on_wide_base"])
    c2.audits()
    c2.losses_vs_fees()
    for name in ("c1", "c3", "timeline", "site"):
        try:
            mod = __import__(f"pipeline.{name}", fromlist=["run"])
        except ModuleNotFoundError:
            continue
        mod.run()
