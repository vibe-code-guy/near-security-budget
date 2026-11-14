"""C3: who can upgrade or move funds, with how many signers, and after what delay (THESIS.md section 5, C3).

The trace is read by hand (data/c3_findings.json). This module checks it against the cached
view calls and computes every number from that raw chain state:
council sizes and thresholds, full-access key counts, auto-update flags, staging durations.
"""
from . import config, universe
from .util import read_json, usd, write_csv, write_json

RAW = config.RAW / "near"
FINDINGS = config.DATA / "c3_findings.json"
OUT = config.DATA / "tables"
INTENTS_SLUG = "near-intents"


# ---------- pure rules (unit-tested) ----------

def to_weight(threshold, total: int) -> int:
    """Sputnik policy.rs WeightOrRatio::to_weight."""
    if isinstance(threshold, list):
        num, den = int(threshold[0]), int(threshold[1])
        return min(num * total // den + 1, total)
    return min(int(threshold), total)


def dao_threshold(policy: dict, kind: str) -> tuple:
    """(votes needed, council size, role name) for the smallest group that can approve `kind`."""
    best = None
    for role in policy["roles"]:
        members = role["kind"].get("Group") if isinstance(role["kind"], dict) else None
        if not members:
            continue
        perms = set(role["permissions"])
        if not perms & {"*:*", "*:VoteApprove", f"{kind}:*", f"{kind}:VoteApprove"}:
            continue
        vp = role.get("vote_policy", {}).get(kind) or policy["default_vote_policy"]
        need = to_weight(vp["threshold"], len(members))
        if best is None or need < best[0]:
            best = (need, len(members), role["name"])
    return best


def full_access_keys(rec: dict):
    keys = rec["view_access_key_list"]
    if keys.get("error"):
        return None  # could not be listed (for example more than 100 keys)
    return sum(1 for k in keys["keys"] if k["access_key"]["permission"] == "FullAccess")


def call_value(rec: dict, method: str):
    for c in rec["calls"]:
        if c["method"] == method:
            return c.get("value"), c.get("error")
    return None, "not called"


def claim_verdicts(rows: list) -> dict:
    """Kill criteria of C3a and C3b, from per-protocol rows."""
    assessed = sum(r["tvl"] for r in rows)
    intents = next(r for r in rows if r["slug"] == INTENTS_SLUG)
    one = [r for r in rows if r["readable"] and r["min_signers"] == 1]
    unread = [r for r in rows if not r["readable"]]
    share_one = sum(r["tvl"] for r in one) / assessed
    share_unread = sum(r["tvl"] for r in unread) / assessed
    if intents["min_signers"] == 1 or share_one > 0.30:
        a = "fails"
    elif share_unread > 0.30:
        a = "can't tell"
    else:
        a = "holds"
    rest = [r for r in rows if r["slug"] != INTENTS_SLUG]
    base = sum(r["tvl"] for r in rest)
    share_delay = sum(r["tvl"] for r in rest if r["delay"] is True) / base
    share_unread_b = sum(r["tvl"] for r in rest if r["delay"] is None) / base
    if share_delay > 0.5:
        b = "holds"
    elif share_delay + share_unread_b > 0.5 and share_unread_b > 0.30:
        b = "can't tell"
    else:
        b = "fails"
    c3 = "holds" if (a, b) == ("holds", "holds") else ("fails" if "fails" in (a, b) else "can't tell")
    return {"C3a": a, "C3b": b, "C3": c3, "assessed_tvl_usd": usd(assessed),
            "intents_min_signers": intents["min_signers"],
            "share_assessed_tvl_one_signer_pct": round(100 * share_one, 1),
            "share_assessed_tvl_unreadable_pct": round(100 * share_unread, 1),
            "c3b_base_tvl_usd": usd(base), "c3b_share_with_enforced_delay_pct": round(100 * share_delay, 1),
            "c3b_share_unreadable_pct": round(100 * share_unread_b, 1)}


# ---------- trace ----------

def pause_signers(p: dict, min_signers) -> str:
    """Fewest signers who can pause: a number read from the trace, or the DAO's own minimum."""
    v = p.get("pause_signers", {}).get("signers")
    if v == "dao":
        return "" if min_signers is None else str(min_signers)
    return "" if v is None else str(v)


def load_raw() -> dict:
    return {p.stem: read_json(p) for p in sorted(RAW.glob("*.json"))}


def check_expectations(findings: dict, raw: dict) -> int:
    n = 0
    for proto in findings["protocols"]:
        for e in proto.get("expect", []):
            value, err = call_value(raw[e["account"]], e["call"])
            assert err is None, (e, err)
            for key in e["path"]:
                value = value[key]
            if isinstance(value, list):
                value = sorted(value)
            want = sorted(e["equals"]) if isinstance(e["equals"], list) else e["equals"]
            assert value == want, f"{proto['slug']}: {e['account']}.{e['call']}{e['path']} is {value!r}, findings say {want!r}"
            n += 1
    return n


def dao_paths(dao: str, kind: str, raw: dict) -> dict:
    rec = raw[dao]
    policy, _ = call_value(rec, "get_policy")
    need, size, role = dao_threshold(policy, kind)
    info, err = call_value(rec, "get_factory_info")
    version, _ = call_value(rec, "version")
    acc = rec["view_account"]
    out = {"dao": dao, "votes_needed": need, "council_size": size, "council_role": role,
           "dao_code": acc.get("global_contract_hash") or acc.get("code_hash"),
           "dao_reported_version": version, "dao_full_access_keys": full_access_keys(rec),
           "auto_update": None if info is None else bool(info["auto_update"]),
           "factory": None if info is None else info["factory_id"], "factory_full_access_keys": None,
           "factory_path_signers": None}
    if info and info["auto_update"]:
        fak = full_access_keys(raw[info["factory_id"]])
        out["factory_full_access_keys"] = fak
        out["factory_path_signers"] = 1 if fak else None
    return out


def run() -> dict:
    findings = read_json(FINDINGS)
    raw = load_raw()
    checked = check_expectations(findings, raw)
    uni = {r["slug"]: r for r in universe.load() if r["chain"] == config.NEAR and r["in_tests"] == "yes"}
    in_scope = [s for s, r in uni.items() if s == INTENTS_SLUG or r["listing_tvl_usd"] >= config.C3_MIN_TVL_USD]
    traced = {p["slug"]: p for p in findings["protocols"]}
    assert sorted(in_scope) == sorted(traced), (in_scope, list(traced))

    rows, table, daos = [], [], []
    for slug in sorted(in_scope, key=lambda s: -uni[s]["listing_tvl_usd"]):
        p, u = traced[slug], uni[slug]
        contract_fak = [full_access_keys(raw[c]) for c in p["contracts"]]
        heights = [raw[c]["view_account"].get("block_height") for c in p["contracts"]]
        direct, via_factory, holders = None, None, []
        for path in p["upgrade"]:
            assert path["kind"] == "dao"
            d = dao_paths(path["holder"], path["proposal_kind"], raw)
            daos.append({"protocol": u["protocol"], **d})
            holders.append(f"{d['dao']} ({d['votes_needed']} of {d['council_size']})")
            direct = d["votes_needed"] if direct is None else min(direct, d["votes_needed"])
            if d["factory_path_signers"]:
                via_factory = d["factory_path_signers"]
        candidates = [x for x in (direct, via_factory) if x]
        if any(contract_fak):
            candidates.append(1)
        min_signers = min(candidates) if (p["readable"] and candidates) else None
        delay = p["delay"]["enforced"]
        rows.append({"slug": slug, "tvl": u["listing_tvl_usd"], "readable": p["readable"],
                     "min_signers": min_signers, "delay": delay})
        table.append({
            "protocol": u["protocol"], "slug": slug, "listing_tvl_usd": usd(u["listing_tvl_usd"]),
            "contracts": " | ".join(p["contracts"]), "block_height": " | ".join(str(h) for h in heights),
            "full_access_keys_on_contracts": " | ".join(str(x) for x in contract_fak),
            "source_readable": "yes" if p["readable"] else "no",
            "upgrade_holder": "; ".join(holders) if holders else "unreadable",
            "signers_via_dao_vote": direct if p["readable"] else "",
            "signers_via_sputnik_factory": via_factory if (p["readable"] and via_factory) else "",
            "min_signers_upgrade_or_move_funds": min_signers if min_signers else "unreadable",
            "one_signer_path": "unreadable" if min_signers is None else ("yes" if min_signers == 1 else "no"),
            "enforced_upgrade_delay": "unreadable" if delay is None else ("yes" if delay else "no"),
            "pause_min_signers": pause_signers(p, min_signers),
            "pause_holder": p.get("pause_signers", {}).get("holder", ""),
            "delay_evidence": p["delay"]["evidence"], "pause": p.get("pause", ""),
            "restricted_paths": " ".join(x["how"] for x in p.get("restricted_paths", [])),
            "other_powers": p.get("other_powers", ""), "source": p["source"],
        })
    not_assessed = [{"protocol": r["protocol"], "slug": s, "listing_tvl_usd": usd(r["listing_tvl_usd"])}
                    for s, r in uni.items() if s not in in_scope]
    v = claim_verdicts(rows)
    factory = raw["sputnik-dao.near"]
    v.update({"claim": "C3", "expectations_checked_against_raw": checked,
              "factory": {"account": "sputnik-dao.near", "full_access_keys": full_access_keys(factory),
                          "owner": call_value(factory, "get_owner")[0],
                          "block_height": factory["view_account"].get("block_height")},
              "not_assessed": not_assessed})
    acl_i = call_value(raw["intents.near"], "acl_get_permissioned_accounts")[0]
    acl_c = call_value(raw["ctl-intents.near"], "acl_get_permissioned_accounts")[0]
    keys_i = raw["intents.near"]["view_access_key_list"]["keys"]
    d_i = next(d for d in daos if d["dao"] == "intents.sputnik-dao.near")
    v["intents_path"] = {
        "contract": "intents.near", "contract_full_access_keys": full_access_keys(raw["intents.near"]),
        "contract_function_call_keys": len(keys_i) - full_access_keys(raw["intents.near"]),
        "dao": d_i["dao"], "dao_votes_needed": d_i["votes_needed"], "dao_council_size": d_i["council_size"],
        "dao_auto_update": d_i["auto_update"], "factory": d_i["factory"], "factory_full_access_keys": d_i["factory_full_access_keys"],
        "controller": acl_i["roles"]["Upgrader"]["grantees"][0],
        "controller_updaters": len(acl_c["roles"]["Updater"]["grantees"]),
        "controller_downgraders": len(acl_c["roles"]["Downgrader"]["grantees"]),
        "controller_releasers": len(acl_c["roles"]["Releaser"]["grantees"]),
        "pause_managers": len(acl_i["roles"]["PauseManager"]["grantees"]),
        "unpause_managers": len(acl_i["roles"]["UnpauseManager"]["grantees"]),
        "block_height": raw["intents.near"]["view_account"].get("block_height")}
    write_csv(OUT / "c3_control.csv", table, list(table[0].keys()))
    write_csv(OUT / "c3_daos.csv", daos, list(daos[0].keys()))
    write_json(OUT / "c3_verdict.json", v)
    print("C3a:", v["C3a"], "| C3b:", v["C3b"], "| C3:", v["C3"])
    return v
