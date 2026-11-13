"""Fixed rules from THESIS.md section 4. Change nothing here without a note in THESIS.md section 10."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
RAW = DATA / "raw"
SITE = ROOT / "site"

LLAMA = "https://api.llama.fi"
NEAR_RPC = "https://free.rpc.fastnear.com"  # listed on docs.near.org/api/rpc/providers
USER_AGENT = "near-security-budget/1.0 (read-only research)"

NEAR = "Near"
PEERS = ["Solana", "Sui", "Aptos", "Base"]
CHAINS = [NEAR] + PEERS

EXCLUDED_CATEGORIES = {"CEX", "Chain", "Risk Curators"}
TOP_N = 10
NEAR_EXTRA_RANKS = 1  # rank 11 on NEAR is looked up and charted, never tested

# chainTvls keys that are not chains
NON_CHAIN_KEYS = {"staking", "pool2", "borrowed", "vesting", "offers", "treasury", "OwnTokens"}

WINDOW_DAYS = 730  # C2 window
C3_MIN_TVL_USD = 10_000_000  # C3 scope
BANDS = [  # C1b, by total TVL of the listing
    ("<$10M", 0, 1e7),
    ("$10M-$100M", 1e7, 1e8),
    ("$100M-$1B", 1e8, 1e9),
    (">$1B", 1e9, float("inf")),
]
MIN_PEERS_PER_BAND = 3
