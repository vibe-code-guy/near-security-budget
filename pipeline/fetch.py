"""`make data`: refresh the raw cache. Read-only GETs and NEAR view calls, no keys.

Every file gets an entry in data/raw/manifest.json: URL or call, retrieval time, SHA-256,
and for NEAR view calls the block height the answer was read at.
"""
import base64
import json
import time
import urllib.error
import urllib.request

from . import config, universe
from .util import read_json, sha256_bytes, utc_now, write_bytes, write_json

MANIFEST = config.RAW / "manifest.json"
TARGETS = config.DATA / "c3_targets.json"


def http_get(url: str, tries: int = 3) -> tuple:
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": config.USER_AGENT, "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=120) as r:
                return r.status, r.read()
        except urllib.error.HTTPError as e:
            if e.code in (400, 404):
                return e.code, e.read()
            last = e
        except Exception as e:  # network hiccup: retry
            last = e
        time.sleep(2 * (i + 1))
    raise RuntimeError(f"GET {url} failed: {last!r}")


def rpc(method: str, params, tries: int = 4) -> dict:
    body = json.dumps({"jsonrpc": "2.0", "id": "1", "method": method, "params": params}).encode()
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(config.NEAR_RPC, data=body,
                                         headers={"Content-Type": "application/json", "User-Agent": config.USER_AGENT})
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)
        except Exception as e:
            last = e
            time.sleep(1.5 * (i + 1))
    raise RuntimeError(f"RPC {method} failed: {last!r}")


def view_call(account: str, method: str, args=None) -> dict:
    """Read-only contract view. Returns {"value"| "error", "block_height"}."""
    r = rpc("query", {"request_type": "call_function", "finality": "final", "account_id": account,
                      "method_name": method,
                      "args_base64": base64.b64encode(json.dumps(args or {}).encode()).decode()})
    if "error" in r:
        return {"error": json.dumps(r["error"], sort_keys=True)[:400]}
    res = r["result"]
    if "error" in res:
        return {"error": res["error"][:400], "block_height": res.get("block_height")}
    raw = bytes(res["result"])
    try:
        value = json.loads(raw.decode("utf-8"))
    except Exception:
        value = {"_non_json_bytes": len(raw), "_sha256": sha256_bytes(raw)}
    return {"value": value, "block_height": res["block_height"]}


def view_account(account: str) -> dict:
    r = rpc("query", {"request_type": "view_account", "finality": "final", "account_id": account})
    return r.get("result") or {"error": json.dumps(r.get("error"), sort_keys=True)[:400]}


def view_keys(account: str) -> dict:
    r = rpc("query", {"request_type": "view_access_key_list", "finality": "final", "account_id": account})
    return r.get("result") or {"error": json.dumps(r.get("error"), sort_keys=True)[:400]}


class Manifest:
    def __init__(self):
        self.data = read_json(MANIFEST) if MANIFEST.exists() else {"files": {}}

    def record(self, path, source: str, body: bytes, **extra):
        key = path.resolve().relative_to(config.ROOT).as_posix()
        self.data["files"][key] = {"source": source, "retrieved_at": utc_now(), "sha256": sha256_bytes(body),
                                   "bytes": len(body), **extra}

    def save(self):
        write_json(MANIFEST, self.data)


def fetch_defillama(m: Manifest) -> None:
    d = config.RAW / "defillama"
    plain = {"hacks.json": "/hacks", "chains.json": "/v2/chains"}
    for chain in config.CHAINS:
        plain[f"chain_tvl_{chain}.json"] = f"/v2/historicalChainTvl/{chain}"
    status, body = http_get(config.LLAMA + "/protocols")
    assert status == 200, status
    write_bytes(d / "protocols.json.gz", body, gz=True)
    m.record(d / "protocols.json.gz", "GET " + config.LLAMA + "/protocols", body, http_status=status,
             note="sha256 and bytes are of the uncompressed response")
    first = not universe.UNIVERSE_CSV.exists()
    now = utc_now()
    if universe.freeze(json.loads(body), snapshot_date=now[:10], retrieved_at=now):
        print("universe frozen:", universe.UNIVERSE_CSV)
    elif first is False:
        print("universe already frozen; not changed")
    for name, path in plain.items():
        status, body = http_get(config.LLAMA + path)
        assert status == 200, (path, status)
        write_bytes(d / name, body)
        m.record(d / name, "GET " + config.LLAMA + path, body, http_status=status)
    # Fees for the NEAR listings in the tests (descriptive metric, THESIS.md section 6)
    for row in universe.load():
        if row["chain"] == config.NEAR and row["in_tests"] == "yes":
            path = f"/summary/fees/{row['slug']}?dataType=dailyFees"
            status, body = http_get(config.LLAMA + path)
            if status != 200:
                body = json.dumps({"http_status": status, "body": body.decode("utf-8", "replace")[:300]}).encode()
            write_bytes(d / "fees" / f"{row['slug']}.json", body)
            m.record(d / "fees" / f"{row['slug']}.json", "GET " + config.LLAMA + path, body, http_status=status)
    m.save()


def fetch_sensitivity(m: Manifest) -> None:
    """Chain TVL series that includes liquid staking and double-counted TVL (C2 sensitivity note only)."""
    d = config.RAW / "defillama"
    for chain in config.CHAINS:
        path = f"/lite/charts/{chain}"
        status, body = http_get(config.LLAMA + path)
        assert status == 200, (path, status)
        write_bytes(d / f"lite_charts_{chain}.json", body)
        m.record(d / f"lite_charts_{chain}.json", "GET " + config.LLAMA + path, body, http_status=status)
    m.save()


def fetch_near(m: Manifest) -> None:
    """Run every view call listed in data/c3_targets.json and cache the answers."""
    if not TARGETS.exists():
        print("no data/c3_targets.json yet; skipping NEAR view calls")
        return
    targets = read_json(TARGETS)
    st = rpc("status", [])["result"]
    out_dir = config.RAW / "near"
    head = {"chain_id": st["chain_id"], "latest_block_height": st["sync_info"]["latest_block_height"],
            "latest_block_time": st["sync_info"]["latest_block_time"], "rpc": config.NEAR_RPC}
    for account, spec in sorted(targets["accounts"].items()):
        rec = {"account_id": account, "retrieved_at": utc_now(), "rpc_head": head}
        acc = view_account(account)
        rec["view_account"] = {k: acc.get(k) for k in ("amount", "locked", "code_hash", "storage_usage",
                                                       "global_contract_hash", "global_contract_account_id",
                                                       "block_height", "error") if k in acc}
        keys = view_keys(account)
        rec["view_access_key_list"] = {"block_height": keys.get("block_height"), "error": keys.get("error"),
                                       "keys": sorted(keys.get("keys", []), key=lambda k: k["public_key"])}
        for k in rec["view_access_key_list"]["keys"]:
            k["access_key"].pop("nonce", None)  # nonces change every transaction; not needed
        rec["calls"] = []
        for call in spec.get("calls", []):
            res = view_call(account, call["method"], call.get("args"))
            rec["calls"].append({"method": call["method"], "args": call.get("args") or {}, **res})
        body = (json.dumps(rec, indent=1, sort_keys=True) + "\n").encode()
        path = out_dir / f"{account}.json"
        write_bytes(path, body)
        m.record(path, f"NEAR RPC view calls on {account} via {config.NEAR_RPC}", body,
                 block_height=rec["view_account"].get("block_height"))
        print("near:", account, rec["view_account"].get("code_hash"),
              f"{len(rec['view_access_key_list']['keys'])} keys", f"{len(rec['calls'])} calls")
    m.save()


def main(what: str = "all") -> None:
    m = Manifest()
    if what in ("all", "defillama"):
        fetch_defillama(m)
    if what in ("all", "defillama", "sensitivity"):
        fetch_sensitivity(m)
    if what in ("all", "near"):
        fetch_near(m)
    print("manifest:", MANIFEST)
