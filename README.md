# near-security-budget

Built at NEAR HACKATHON, track: Investment Thesis (`thesis`).

## What it is

A data-backed test of one investment thesis for NEAR, with a static dashboard
and a pipeline anyone can re-run without credentials.

> NEAR's long-term value rests on being trusted to settle agent money. That
> trust is measurable as security budget: what the ecosystem pays to find bugs,
> and who can stop or change the contracts, relative to the value they secure.

Three claims, each written as "NEAR meets the peer bar" (peers: Solana, Sui,
Aptos, Base), were fixed with kill criteria **before** the data was pulled:

| Claim | Question | Status |
|---|---|---|
| C1 Bounty coverage | Are NEAR's ten largest protocols covered by public bug bounties as well as peers', size for size? | computed, with a sensitivity run (lookups are incomplete, see below) |
| C2 Incident record | Has NEAR lost no more to hacks over 24 months, relative to the value it held? | computed |
| C3 Control | Can a single signer upgrade or drain `intents.near` or the largest NEAR protocols, and is there an upgrade delay? | computed |

The claims, tests, limits and the author's conflict of interest are in
[`THESIS.md`](THESIS.md). Verdicts are the registered kill criteria applied by
code to the numbers; nothing is scored by hand.

## The problem

Agents that hold and move money need a settlement layer whose contracts cannot
be quietly changed or drained. "Is this chain secure?" is usually answered with
opinion. This project answers a narrower question with public data: how much is
paid to find bugs, how much has been lost, and how many keys stand between an
attacker and the contracts, compared with the value at stake and with peers.

## Try it: do X, see Y

Requirements: Python 3.9 or newer. Nothing to install, no API keys, no wallet.

1. **Open the dashboard.** Open `site/index.html` in a browser (double-click; no
   server needed).
   See: three tiles at the top, one per claim, each with a verdict
   (holds / fails / can't tell / pending) and the numbers behind it.
2. **Rebuild everything from the cached raw data.** Run `make all` (or
   `python -m pipeline build && python -m unittest discover -s tests -q`).
   See: the lines `C2: fails | NEAR lower/upper %/yr: 8.378968 8.378968 | peer
   median: 2.374327 2.765235`, `C3a: fails | C3b: fails | C3: fails`,
   `C1a: holds | C1b: holds | C1: holds | coverage NEAR 89.06% vs peer median
   41.79% | score 98.92%`, `C1 sensitivity (not registered): can't tell`,
   `site/data.js written`, and the tests ending in `OK`. `git status` shows no
   changed files: the committed tables and dashboard data are exactly what the
   code produces.
3. **Check C2 by hand.** Open `data/tables/c2_hacks_attributed.csv` and filter
   `chain = Near`, `in_24m_window = yes`.
   See: three rows (Rhea Lend $18.4M, Sweat Foundation $3.5M, NEAR Intents
   $3.8M). Their sum, annualised and divided by NEAR's mean headline TVL in
   `data/tables/c2_loss_rates.csv`, is the 8.38% on the dashboard.
4. **Check C3 against the chain yourself.** Run this read-only call (no
   account needed):
   ```
   curl -s https://free.rpc.fastnear.com -H 'Content-Type: application/json' -d '{"jsonrpc":"2.0","id":"1","method":"query","params":{"request_type":"view_access_key_list","finality":"final","account_id":"sputnik-dao.near"}}'
   ```
   See: the access keys of the Sputnik DAO factory, with `"permission":"FullAccess"`
   on each (three when this was written). Then
   ```
   curl -s https://free.rpc.fastnear.com -H 'Content-Type: application/json' -d '{"jsonrpc":"2.0","id":"1","method":"query","params":{"request_type":"call_function","finality":"final","account_id":"intents.sputnik-dao.near","method_name":"get_factory_info","args_base64":"e30="}}'
   ```
   See: a `result` byte array that decodes to
   `{"factory_id":"sputnik-dao.near","auto_update":true}`. The dashboard's C3
   section explains why those two facts together mean one key.
5. **Refresh the data (optional, needs network).** Run `make data`.
   See: every file under `data/raw/` re-fetched and `data/raw/manifest.json`
   updated with retrieval times and NEAR block heights. The frozen universe
   (`data/universe.csv`) is not changed. Numbers will move with the market;
   the committed cache is what the registered results use.
6. **Check the pre-registration.** Run
   `git show f84b548:THESIS.md | sha256sum`.
   See: `2b99cec36f2b2d575367d2e053d006a3495df0fcbffc0294b52dd77ff921b58b`, the
   hash stored on NEAR and timestamped below.

## How NEAR data is used

- **Read-only view calls on NEAR mainnet** (`https://free.rpc.fastnear.com`,
  listed in the NEAR docs) for 54 accounts: `view_account`,
  `view_access_key_list`, and contract views `acl_get_permissioned_accounts`,
  `pa_all_paused`, `up_get_delay_status` (near-plugins), `get_policy`,
  `get_factory_info` (Sputnik DAO), `get_owner`, `get_contracts_metadata`
  (Sputnik factory), and owner views of each protocol. Answers are cached in
  `data/raw/near/` with the block height each was read at.
- **Open-source contract code** read at named commits to confirm what each role
  can do: `near/intents`, `near/near-plugins`, `near-daos/sputnik-dao-contract`,
  `aurora-is-near/aurora-controller-factory`, `Near-One/omni-bridge`, and the
  protocols' own repositories. The hand-read trace is `data/c3_findings.json`;
  `pipeline/c3.py` checks it against the cached chain state.
- **NEAR transactions** for the case-study timeline (pause, release
  registration, upgrade and unpause calls on `intents.near` and its upgrade
  controller), with a source for every timestamp.
- **The pre-registration is anchored on NEAR**: the hash of `THESIS.md` is
  stored under `near-thesis.near` in SocialDB (`social.near`).
- **DefiLlama** (free, keyless) for TVL per chain and protocol, hack records,
  audits and fees.

## Pre-registration

The claims and kill criteria were fixed before the data was pulled.

| Event | When (UTC) | Where to check |
|---|---|---|
| Registration commit `f84b54871db3b51f5db5ff113b34ef0f76745f56` | 2026-11-13 06:45:58 | `git log`; SHA-256 of `THESIS.md` at that commit is `2b99cec36f2b2d575367d2e053d006a3495df0fcbffc0294b52dd77ff921b58b` |
| OpenTimestamps stamp of that text | 2026-11-13 07:27 | `registration/THESIS.f84b548.md.ots`; upgraded to Bitcoin attestations in blocks 975645, 975648 and 975658 |
| First data pull | 2026-11-13 07:28:54 | `data/raw/manifest.json`, retrieval time of every file |
| On-chain anchor on NEAR | 2026-11-13 11:41:07 | account `near-thesis.near`, transaction [`DsdB2BqHAHxyY2Ud4GYcek7JirLYMJz2tLY1iDNAVXji`](https://nearblocks.io/txns/DsdB2BqHAHxyY2Ud4GYcek7JirLYMJz2tLY1iDNAVXji), block 224358450 |

**The NEAR anchor came after the first data pull**, by about four hours. It
proves the text existed at 11:41 UTC, not that it preceded the data. The
evidence that the text preceded the data is the OpenTimestamps proof (stamped
about two minutes before the first pull) and the git history. Commit dates are
set by the author's machine, so they are evidence of order, not proof.

Some things were already known when the claims were registered (for example
the NEAR Intents bounty ceiling, the October loss, and the state of
`intents.near` seen while checking endpoints). `THESIS.md` section 3 lists them.
Anything added after registration is listed in section 10.

Read the anchor back (view call, no account needed):

```
near contract call-function as-read-only social.near get json-args '{"keys":["near-thesis.near/near-security-budget/**"]}' network-config mainnet now
```

Check the timestamp: `pip install opentimestamps-client`, then
`ots verify registration/THESIS.f84b548.md.ots` (needs a Bitcoin node), or drop
the `.md` and `.ots` files on https://opentimestamps.org.

## Repository layout

| Path | What |
|---|---|
| `THESIS.md` | The claims, kill criteria, what was known beforehand, limits, changes after registration |
| `site/index.html`, `site/data.js` | Static dashboard; `data.js` is generated |
| `pipeline/` | `fetch.py` (`make data`), `universe.py`, `c2.py`, `c3.py`, `timeline.py`, `site.py`, `build.py` |
| `tests/` | Unit tests of the attribution, threshold and verdict rules |
| `data/universe.csv` | The 51 listings, frozen at the first data pull |
| `data/bounties.csv` | Bounty terms per listing (input to C1). Filled on 2026-11-14 by an AI assistant with web access, not by hand; the author checked the four NEAR programme pages himself. 24 of 51 rows were entered as "not checked" |
| `data/bounty_status_rules.json` | How not-live and unfinished rows count in C1, decided after the table was seen (`THESIS.md` section 10) |
| `data/c3_targets.json`, `data/c3_findings.json` | Accounts read for C3, and the hand-read control trace |
| `data/timeline_events.json` | Case-study rows and their sources |
| `data/raw/` | Cached raw responses and `manifest.json` (source, retrieval time, SHA-256, block height) |
| `data/tables/` | Every output table and verdict file |
| `registration/` | The registered text and its OpenTimestamps proof |

GitHub Pages can serve the dashboard from the `site/` folder once the
repository is public; it is not enabled.

## Libraries used

- Python standard library only (`urllib`, `json`, `csv`, `gzip`, `unittest`).
- The dashboard is plain HTML, CSS and JavaScript with hand-written SVG charts;
  no framework, no CDN, no build step.
- `opentimestamps-client` (Python) was used once to stamp the registered text.
  It is not needed to run anything.

## Ground rules

- Read-only. No keys, no transactions, no testing of any vulnerability, nothing
  sent to any contract. Only published bounty terms, public source code and
  public chain state are analysed.
- No number is invented. Where something cannot be computed, `THESIS.md` and
  the dashboard say so.

## How this was built

Claude Code (Anthropic's coding agent) wrote the code and drafted the documents
in this repository under the author's direction. The author chose the thesis
and approved the claims and kill criteria. The bounty table was filled by an AI
assistant with web access, not by hand; the author opened the four NEAR
programme pages himself (Rhea, NEAR Intents, NEAR Intents: Bridges, Meta Pool)
and the maximums match. Commits carry no co-author line, so this section is the
disclosure.

## License

MIT, see `LICENSE`.
