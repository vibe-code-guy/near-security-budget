"""Protocol universe (THESIS.md section 4): top listings per chain, frozen at the first data pull."""
from . import config
from .util import read_csv, read_json, usd, write_csv, write_json

UNIVERSE_CSV = config.DATA / "universe.csv"
SNAPSHOT_JSON = config.DATA / "snapshot.json"
BOUNTIES_CSV = config.DATA / "bounties.csv"

COLUMNS = ["chain", "rank", "in_tests", "protocol", "slug", "defillama_id", "category", "parent",
           "listing_tvl_usd", "total_tvl_usd", "audits_flag", "audit_links", "defillama_url"]

BOUNTY_COLUMNS = ["chain", "protocol", "slug", "defillama_url", "listing_tvl_usd", "total_tvl_usd",
                  "status", "platform", "url", "max_critical_usd", "funds_at_risk_pct", "cap_rule",
                  "payout_terms", "payout_token", "vesting", "checked_sources", "retrieved_at", "notes"]


def chain_tvl(p: dict, chain: str) -> float:
    return float((p.get("chainTvls") or {}).get(chain) or 0)


def eligible(p: dict) -> bool:
    return p.get("category") not in config.EXCLUDED_CATEGORIES


def build(protocols: list) -> list:
    rows = []
    for chain in config.CHAINS:
        listed = [p for p in protocols if eligible(p) and chain_tvl(p, chain) > 0]
        listed.sort(key=lambda p: (-chain_tvl(p, chain), p["slug"]))
        n = config.TOP_N + (config.NEAR_EXTRA_RANKS if chain == config.NEAR else 0)
        for rank, p in enumerate(listed[:n], 1):
            rows.append({
                "chain": chain, "rank": rank, "in_tests": "yes" if rank <= config.TOP_N else "no",
                "protocol": p["name"], "slug": p["slug"], "defillama_id": p["id"],
                "category": p.get("category"), "parent": (p.get("parentProtocol") or "").replace("parent#", ""),
                "listing_tvl_usd": usd(chain_tvl(p, chain)), "total_tvl_usd": usd(p.get("tvl") or 0),
                "audits_flag": p.get("audits"), "audit_links": len(p.get("audit_links") or []),
                "defillama_url": f"https://defillama.com/protocol/{p['slug']}",
            })
    return rows


def eligible_total(protocols: list, chain: str) -> tuple:
    listed = [p for p in protocols if eligible(p) and chain_tvl(p, chain) > 0]
    return len(listed), sum(chain_tvl(p, chain) for p in listed)


def freeze(protocols: list, snapshot_date: str, retrieved_at: str, force: bool = False) -> bool:
    """Write data/universe.csv once. Later pulls never change it."""
    if UNIVERSE_CSV.exists() and not force:
        return False
    write_csv(UNIVERSE_CSV, build(protocols), COLUMNS)
    totals = {}
    for chain in config.CHAINS:
        n, tot = eligible_total(protocols, chain)
        totals[chain] = {"eligible_listings": n, "eligible_listing_tvl_usd": usd(tot)}
    write_json(SNAPSHOT_JSON, {"snapshot_date": snapshot_date, "protocols_retrieved_at": retrieved_at,
                               "eligible_totals": totals})
    return True


def load() -> list:
    rows = read_csv(UNIVERSE_CSV)
    for r in rows:
        r["rank"] = int(r["rank"])
        r["listing_tvl_usd"] = float(r["listing_tvl_usd"])
        r["total_tvl_usd"] = float(r["total_tvl_usd"])
        r["audit_links"] = int(r["audit_links"])
    return rows


def snapshot() -> dict:
    return read_json(SNAPSHOT_JSON)


def write_bounty_template() -> bool:
    """Empty lookup table for the author to fill by hand. Never overwrites an existing file."""
    if BOUNTIES_CSV.exists():
        return False
    rows = sorted(load(), key=lambda r: (-r["listing_tvl_usd"], r["slug"]))
    out = [{"chain": r["chain"], "protocol": r["protocol"], "slug": r["slug"], "defillama_url": r["defillama_url"],
            "listing_tvl_usd": usd(r["listing_tvl_usd"]), "total_tvl_usd": usd(r["total_tvl_usd"])} for r in rows]
    write_csv(BOUNTIES_CSV, out, BOUNTY_COLUMNS)
    return True
