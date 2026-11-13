# THESIS.md

**Status: pre-registration.** This file was written and committed on 2026-11-13,
before any bounty terms, hack totals, fee totals or control data were pulled for
analysis, apart from what section 3 lists. Sections 1 to 8 are fixed at the
registration commit. Section 9 (evidence and verdicts) is empty on purpose and
is filled in later; the git history shows the order. Any later change to sections 1 to 8 is listed in
section 10 with its reason.

To check the registered text: `git show <registration commit>:THESIS.md | sha256sum`.
The commit and hash are recorded in `README.md`.

## 1. Thesis

NEAR's long-term value rests on being trusted to settle agent money. That trust
is measurable as security budget: what the ecosystem pays to find bugs, and who
can stop or change the contracts, relative to the value they secure.

The thesis is conditional. NEAR is investable as the settlement layer for agent
money only if its security budget is at least in line with the chains it
competes with. Three claims test whether that is true today. Each is written as
"NEAR meets the peer bar", so that "fails" is a clean outcome.

Peers: Solana, Sui, Aptos, Base.

The peers were chosen before any data was pulled: Solana and Base as the large
incumbents, Sui and Aptos as L1s closer to NEAR's size. For an investor the
outcome is a discount or its absence. If the claims hold, NEAR's
settlement-layer case needs no security discount against these peers. If one
fails, the gap is the discount, and section 7 says what would close it.

## 2. Conflict of interest

The author is a bug bounty hunter and would benefit from higher bounties on
NEAR. A finding that NEAR under-pays for security is the finding the author is
inclined to want. That is why the claims, the tests and the kill criteria are
fixed here before the data is pulled, and why what the author already knew is
listed in section 3.

## 3. Known before registering

From the author, before registering:

- HackenProof's "NEAR Intents: Smart Contracts" page listed a critical ceiling
  of $300,000, with High and Critical rewards capped at 10% of affected funds,
  and the company entitled to pay in NEAR vested over one year
  (https://hackenproof.com/programs/near-intents-smart-contracts, seen via
  search results, not re-read today).
- Rekt's write-up noted that the "NEAR Intents: Bridges" page shows $300,000 in
  its reward table and $100,000 in its written rules
  (https://rekt.news/near-intents-rekt).
- The loss of about $3.8M on 2026-10-01 and the "fixed within an hour of
  detection" claim came from news reports of Illia Polosukhin's statement
  (https://cryptonews.net/news/security/33526432/).
- A public claim by another hackathon project, Docket
  (https://github.com/aditi3175/docket): full-access keys on the Sputnik factory
  `sputnik-dao.near` can replace the code of auto-updating DAOs without a vote,
  including the DAOs behind Meta Pool and LiNEAR, and the fix
  (near-daos/sputnik-dao-contract PR #233) was merged but not deployed. Not
  checked here yet. Part of C3a's answer was therefore claimed in public before
  registration.

Live programme pages are re-read at the data stage, and `data/bounties.csv`
records what they show then, with retrieval dates.

Seen while checking that the endpoints work (2026-11-13, between 04:54 and
06:15 UTC; DefiLlama protocols and hacks pulled at 04:54 UTC, NEAR RPC at block
224,316,343, 04:56 UTC):

- The DefiLlama protocol names and TVL rankings in appendix B.
- Five hack rows that name NEAR or a NEAR protocol in `api.llama.fi/hacks`:
  Ref Finance 2021-08-15 $3,203,000; Skyward Finance 2022-11-02 $3,000,000;
  Rhea Lend 2026-04-16 $18,400,000; Sweat Foundation 2026-04-29 $3,500,000;
  NEAR Intents 2026-10-01 $3,800,000 (tagged chain `BSC`, not Near).
- The schema of the hacks data and its twelve most recent rows. No hack totals
  for any peer chain were computed.
- That DefiLlama has fee data for `rhea-lend`, `near-intents` and `rhea-dex`,
  starting 2025-05-19, 2025-05-10 and 2024-09-11, and none for `meta-pool-near`
  or `linear-protocol`. The all-time fee totals of those three, and the one-year
  fee totals of the NEAR listings in the fees overview, were printed.
- The current control state of `intents.near`. This is a finding, not a test:
  - The contract account has 9 access keys, all function-call keys limited to
    `execute_intents`. It has no full-access key.
  - Super-admins: `intents.sputnik-dao.near` and `intents.near` itself.
  - Role `DAO` is held by `intents.sputnik-dao.near`: a Sputnik DAO with a
    5-member council and a threshold of 3 for every proposal kind named in its
    policy (the default for other kinds is more than half of the council).
  - Role `Upgrader` is held by the contract `ctl-intents.near`. On that
    contract, role `Updater` has one grantee and role `Downgrader` has two, all
    64-character implicit accounts; its `DAO` role is held by
    `intents.sputnik-dao.near`. What those roles allow has not been read yet.
  - Role `PauseManager` has seven grantees (six implicit accounts and
    `pm.bridge.near`). Role `UnpauseManager` has none.
  - In the source (`near/intents` at commit `fce0936`, `contracts/defuse`):
    pause needs `DAO` or `PauseManager`; unpause needs `DAO` or
    `UnpauseManager`; `upgrade` needs `DAO` or `Upgrader` and deploys the new
    code in the same call; `admin_call` (arbitrary function calls and transfers
    made by the contract) needs `DAO`.
  - `up_get_delay_status` does not exist on `intents.near`. The contract does
    not use the near-plugins upgrade module, so there is no staging delay.

No ratio, loss rate or peer comparison had been computed when this file was
committed. No bounty page and no Sputnik DAO or factory state beyond the
`get_policy` result above had been read for this project.

## 4. Universe and data rules

**Protocol.** One DefiLlama listing from `GET api.llama.fi/protocols`. Listings
are not merged into parent families.

**Listing TVL on a chain.** `chainTvls[<Chain>]` for the exact keys `Near`,
`Solana`, `Sui`, `Aptos`, `Base`. Suffixed keys (`-staking`, `-borrowed`,
`-pool2` and similar) are ignored.

**Total TVL of a listing.** Its `tvl` field: all chains.

**Excluded categories.** `CEX` (exchange wallets are not protocols on the
chain), `Chain`, and `Risk Curators` (curator TVL sits inside other listed
protocols).

**Top 10.** The ten listings with the largest listing TVL on the chain after
exclusions. For NEAR the listing ranked 11 is also looked up and charted, so the
bounty table has 51 rows, but every NEAR test uses ranks 1 to 10 only. A listing
that is in the top 10 of two chains is counted on each.

**Freeze.** The universe is frozen from the first `make data` run after this
commit and written to `data/universe.csv`. Appendix B is the provisional list.

**TVL basis.** C1 and C3 use listing TVL. C2 uses DefiLlama's headline chain TVL
history, `GET api.llama.fi/v2/historicalChainTvl/<Chain>`, on every chain. The
two NEAR figures differ (2026-11-13 04:54 UTC: $470.8M summed over the 30
eligible listings, $159.7M headline from `api.llama.fi/v2/chains`, because the
headline leaves out liquid staking and double-counted TVL). The dashboard shows
both.

**Snapshot date.** The date of the first `make data` run. `make data` records
the retrieval time of every file and the NEAR block height of every view call.

**Sources.** Free and keyless. DefiLlama for TVL, audits, hacks and fees. NEAR
mainnet RPC `https://free.rpc.fastnear.com` (read-only view calls). Public
source code. Bounty terms from `data/bounties.csv`, filled by hand by the author.

## 5. Claims and kill criteria

### C1. Bounty coverage

*NEAR's ten largest DeFi protocols are covered by live public bug bounties at
least as well as the ten largest on Solana, Sui, Aptos and Base.*

**Bounty table.** `data/bounties.csv`, one row per listing (51 rows), columns:
`chain, protocol, slug, status, platform, url, max_critical_usd, cap_rule,
payout_terms, payout_token, vesting, checked_sources, retrieved_at, notes`.

Lookup rule, applied to every listing in the same order: Immunefi, HackenProof,
Cantina, Sherlock, HackerOne, then the protocol's own security page and its
GitHub `SECURITY.md`. `checked_sources` lists what was checked.

`status` is one of:

- `live`: a public programme is open and its scope includes the contracts that
  hold this listing's TVL.
- `none_found`: nothing found in any of the sources above, or a programme
  exists but is closed or does not cover this listing. Counts as zero.
- `undetermined`: a programme exists but its terms are not public.

`max_critical_usd` is the effective maximum payout for a critical finding, in
USD:

- Where the terms state a fixed maximum, it is that figure.
- Where the terms tie the payout to funds at risk with a cap, it is
  min(cap, percentage x the listing's total TVL at the snapshot). The row is
  flagged as derived when the percentage leg binds. It is not simply the cap.
- Where the terms give a percentage of funds at risk with no cap, it is that
  percentage of the listing's total TVL at the snapshot, flagged as derived.
- If several live programmes cover a listing, the highest maximum among those
  in scope is used and the others are noted.
- If a programme page contradicts itself, the higher figure is used and both
  are recorded.
- If no USD figure can be read from the published terms, the row is
  `undetermined`.

The rules on several programmes and on contradictions favour the protocol on
every chain, which is the right direction given section 2. Payout token and
vesting are recorded and reported. Payouts are not discounted for them.

**C1a, coverage share.** For each chain: listing TVL of top-10 protocols with
`status = live`, divided by top-10 listing TVL.

**C1b, size-matched bounty ratio.**

- Ratio of a listing = `max_critical_usd` / total TVL of the listing. Zero if
  `none_found`.
- Each listing is put in a band by the total TVL used in its ratio: under $10M,
  $10M to $100M, $100M to $1B, over $1B.
- Peer protocols are the 40 peer listings, pooled over the four chains. A band
  with fewer than 3 peer protocols is merged into the band below it (the lowest
  band merges into the one above), repeated until every band has at least 3.
  `undetermined` peers are left out of the count and the median.
- Peer bar of a band = the median ratio of the peer protocols in it.
- NEAR score = listing TVL of NEAR top-10 protocols whose ratio is at or above
  their band's bar, divided by NEAR top-10 listing TVL. An `undetermined` NEAR
  protocol does not count as at or above.
- If a band's bar is zero, a NEAR protocol with no bounty meets it. Those cases
  are counted and reported separately.

**Fails if** NEAR's coverage share is more than 10 percentage points below the
median coverage share of the four peers, or the NEAR score is below 50%.

**Holds if** neither condition is met.

**Can't tell if** `undetermined` rows hold more than 20% of top-10 listing TVL
on NEAR, or on two or more peer chains.

**Chart.** All 51 listings, maximum critical payout against total TVL, both axes
logarithmic, coloured by chain. Listings with no bounty cannot sit on a log
axis; they are drawn on a labelled baseline strip.

### C2. Incident record

*Over the last 24 months NEAR has lost no more to hacks, relative to the value
it held, than Solana, Sui, Aptos and Base.*

**Window.** The 730 days ending on the snapshot date.

**Losses.** `amount` (USD) from `GET api.llama.fi/hacks` for rows dated in the
window. Rows with no amount count as zero and are listed. `returnedFunds` is
shown separately and not netted. Rows with `targetType = CEX` are excluded,
because the headline TVL in the denominator excludes exchange wallets.

**Attribution.** A hack is attributed to a chain by either route:

- Chain tag: its `chain` list names the chain (case-insensitive).
- Protocol id: its `defillamaId` resolves to a listing in `/protocols`. The hack
  then goes to the one chain holding the largest share of that listing's TVL at
  the snapshot, and to no other chain by this route.

**Bounds.** Multi-chain hacks are not split.

- Lower bound: hacks tagged with that chain only, plus hacks attributed to the
  chain by protocol id.
- Upper bound: the lower bound plus, at full amount, every hack whose tag list
  names the chain together with others.

**Loss rate.** Losses in the window, divided by the mean of the daily headline
chain TVL over the same window, annualised (multiplied by 365 / 730). Unit: per
cent of average TVL per year.

**Fails if** NEAR's loss rate is above the median of the four peers on both
bounds.

**Holds if** it is at or below the peer median on both bounds.

**Can't tell if** the comparison flips between the bounds.

The verdict rests on the loss rate alone.

### C3. Control

*For `intents.near` and the largest NEAR protocols, no single signer can upgrade
the contract or move user funds, and upgrades are subject to an on-chain delay.*

**Scope.** `intents.near`, plus every NEAR listing with at least $10M of listing
TVL on NEAR at the snapshot. "Assessed TVL" is the listing TVL of those
protocols. The rest of the top 10 is listed as not assessed.

**Contracts.** For each listing, the NEAR accounts that hold or control its TVL,
taken from the listing's DefiLlama adapter source and the protocol's own
documentation, and confirmed with `view_account`.

**Recorded per contract.**

- Access keys on the contract account, split into full-access and function-call
  (`view_access_key_list`). A full-access key is a one-signer path to upgrade
  and to move funds.
- Holders of the pause, unpause, upgrade and arbitrary-call powers. Where
  near-plugins is used: `acl_get_super_admins`, `acl_get_grantees`,
  `acl_get_permissioned_accounts`, `pa_all_paused`, `up_get_delay_status`.
  What each role can do is confirmed in the open source code.
- What each holder is, traced until it ends in one of: access keys (counted); a
  Sputnik DAO (`get_policy`: members and threshold for the relevant proposal
  kind, then the factory check below); a multisig contract (its confirmation
  count); or a contract whose source cannot be read (marked unreadable).
  Controller contracts such as `ctl-intents.near` are traced the same way, down
  to keys or DAO thresholds.
- A Sputnik DAO is not the end of a trace. For every Sputnik DAO in a control
  path, including `intents.sputnik-dao.near`, the trace also records whether
  the DAO's own code can be replaced without a proposal:
  - `get_factory_info` on the DAO (`factory_id`, `auto_update`);
  - `get_owner` on that factory, and the factory account's access keys;
  - the update path as read in `near-daos/sputnik-dao-contract`: `update` in
    `sputnikdao2`, and `update` and `store` in `sputnikdao-factory2`;
  - which code version each DAO actually runs, from its code hash. The `main`
    branch is not assumed to be what is deployed.

  A path through the factory counts toward minimum signers in C3a. Where this
  confirms the claim made by Docket (section 3), Docket is credited. View calls
  only.
- Minimum signers for each of pause, upgrade and move funds: the smallest number
  of distinct keys, over all paths, that is enough to do it.
- Enforced delay on upgrades: a non-zero minimum time between an upgrade being
  staged or approved on chain and taking effect, which the upgraders cannot skip
  in the same step. A near-plugins staging duration above zero counts. A Sputnik
  `proposal_period` does not: it is a voting expiry. A full-access key on the
  contract account bypasses any delay, so the delay then does not count.

**C3a, signers. Fails if** `intents.near`, or protocols holding more than 30% of
assessed TVL, have a one-signer path to upgrade or to move user funds. A
one-signer pause does not count against it. **Holds** otherwise.

**C3b, delay. Holds if** protocols holding more than half of assessed TVL,
excluding `intents.near`, enforce an on-chain delay on upgrades. **Fails**
otherwise. `intents.near` is left out of this test because its answer was
already known (section 3).

**C3 holds** only if C3a and C3b both hold. **It fails** if either fails.

**Can't tell if** contracts holding more than 30% of the TVL in a test are
closed-source or their roles cannot be read.

**The trade-off.** An immediate upgrade path cuts both ways. The author's
understanding, from the report cited in section 3 and to be confirmed or
corrected with sourced timestamps in the case study, is that the same-call upgrade is what allowed the 2026-10-01 patch to
land within the hour. A delay that protects users from an unwanted upgrade also
slows a wanted one. C3b measures whether a delay exists; it does not say that a
delay is always better.

## 6. Descriptive metrics (no verdict)

- **Audits.** Per listing: DefiLlama's `audits` flag and the number of
  `audit_links`. `audits` is a 0 to 3 flag, not a count, and the links
  under-report. Shown per chain, with these limits stated.
- **All-time hack losses** per chain, by the C2 attribution rules.
- **Hack losses against fees.** For each NEAR top-10 listing with data at
  `GET api.llama.fi/summary/fees/<slug>?dataType=dailyFees`: hack losses
  attributed to that listing by protocol id, divided by its fees, both over the
  C2 window clipped to the first day of fee data. The clipped start date is
  shown. Listings with no fee data are listed as such.
- **Payout token and vesting** of each bounty.
- **L2BEAT Stage 1 Security Council yardstick.** For each control set found in
  C3, a column compares it with L2BEAT's published Stage 1 requirements (see
  appendix A for the source text): a multisig of at least 8 participants; a 75%
  threshold; participants from different entities, with addresses of one entity
  counted once; identities or pseudonyms publicly disclosed; and an exit window
  of at least 5 days for upgrades started by anyone other than the council.
  Entity diversity cannot be read from chain state and is marked as such. The
  framework was written for Ethereum rollups. It is used here as a familiar
  yardstick, not as a rating of NEAR applications.
- **Case study: the 2026-10-01 NEAR Intents exploit.** A timeline from chain
  data and the official postmortem, with a source for every timestamp.

## 7. What would change my mind

- The thesis is supported on this measure only if C1, C2 and C3 all hold.
- If any claim fails, the write-up says which one, by how much, and what would
  have to change on NEAR for it to hold.
- The author's prior, from section 3, is that C1 fails. If C1 holds, that prior
  was wrong and the write-up says so.
- If a claim comes out "can't tell", it is reported as that, not as a pass.
- If the evidence shows that the yardsticks themselves do not track safety in
  this sample (for example, peers with higher bounty ratios did not lose less),
  that is reported as evidence against the framing of the thesis.

## 8. Limits

- Fifty-one listings and five chains. Nothing here shows that a bounty, an audit
  or a delay causes fewer losses.
- One bounty programme can cover several sibling listings (for example three
  Rhea listings on NEAR, three Jupiter listings on Solana). Each listing's ratio
  uses the full programme maximum over that listing's own TVL, which overstates
  per-dollar coverage for families on every chain.
- A published maximum is a ceiling, not what is paid. Paid amounts are mostly
  not public.
- "None found" means not found in the listed sources on the retrieval date.
- Bands are coarse. Within a band the ratio still falls with size, which favours
  the smaller listings; NEAR's largest sit at the low end of the $100M to $1B
  band.
- TVL is a snapshot for C1 and C3. Bands and ranks would move with the market.
- DefiLlama's hack list is curated by hand: coverage, amounts and chain tags are
  theirs. The NEAR Intents exploit is tagged `BSC`, which is why the protocol-id
  route exists.
- Protocol-id attribution uses the listing's largest chain today, not at the
  time of the hack.
- Headline chain TVL excludes liquid staking and double-counted TVL on every
  chain alike, but those make up different shares of each chain.
- Twenty-four months is short. One large hack moves a small chain's loss rate a
  lot.
- A key seen on chain may be a hardware wallet or an MPC setup shared by several
  people, or several keys may belong to one person. Chain state cannot tell.
- Source code is read at a named commit. The deployed code is identified by its
  code hash; whether the two match is checked where a reproducible build
  exists, and stated as unverified where it does not.
- Control findings describe who can act, not whether they would.
- If the control trace finds what looks like an unintended privilege rather than
  a documented design choice, it is reported to the project first and left out
  of the published results until resolved, and section 10 records that
  something was withheld.
- Read-only. No keys, no transactions, no testing of any vulnerability, nothing
  sent to any contract.

## 9. Evidence and verdicts

Not written yet. No data had been pulled for analysis when this file was
registered.

| Claim | Evidence for | Evidence against | Verdict (holds / fails / can't tell) |
|---|---|---|---|
| C1 | | | |
| C2 | | | |
| C3 | | | |

## 10. Changes after registration

None.

## Appendix A. What was verified before registering (2026-11-13)

| What | Result |
|---|---|
| `GET api.llama.fi/protocols` | 200; 9,026 listings; `chainTvls`, `tvl`, `category`, `audits`, `audit_links` |
| `GET api.llama.fi/protocol/<slug>` | 200; `ref-finance` now resolves to "Rhea Dex" (`rhea-dex`) |
| `GET api.llama.fi/hacks` | 200; 1,351 rows; `amount` in USD, `chain` list, `targetType`, `returnedFunds`; `defillamaId` numeric on 583 rows, 576 of which resolve to a listing |
| `GET api.llama.fi/v2/chains` | 200; headline TVL per chain |
| `GET api.llama.fi/v2/historicalChainTvl/<Chain>` | 200 for Near, Solana, Sui, Aptos, Base; one point per day with no gaps; Near starts 2021-08-20, Sui 2023-05-06 |
| `GET api.llama.fi/summary/fees/<slug>?dataType=dailyFees` | 200 with a daily `totalDataChart` for `rhea-lend`, `near-intents`, `rhea-dex`; 400 "not found" for `meta-pool-near`, `linear-protocol` |
| NEAR RPC `https://free.rpc.fastnear.com` | Listed on `docs.near.org/api/rpc/providers`; `status` returned mainnet; not archival |
| `query view_account`, `query view_access_key_list` | Return for `intents.near` |
| `acl_get_super_admins(skip, limit)`, `acl_get_grantees(role, skip, limit)`, `acl_get_admins(role, skip, limit)`, `acl_get_permissioned_accounts()`, `acl_role_variants()`, `pa_all_paused()` | Signatures read in `near/near-plugins` (`access_controllable.rs`, `pausable.rs`); all return on `intents.near` |
| `up_get_delay_status()` | Signature read in near-plugins `upgradable.rs`; `MethodNotFound` on `intents.near` |
| `get_policy()` | Read in `near-daos/sputnik-dao-contract`, `sputnikdao2/src/views.rs`; returns on `intents.sputnik-dao.near` |
| Sputnik DAO `get_factory_info()` and `update()`; factory `get_owner()`, `update(account_id, code_hash)`, `store()`, `get_default_code_hash()` | Names read in `near-daos/sputnik-dao-contract` at commit `5434a59dec23ee0c49df8c8c4350c208a7e75b0b` (`sputnikdao2/src/lib.rs`, `sputnikdao2/src/upgrade.rs`, `sputnikdao-factory2/src/lib.rs`). Not called on chain yet, and what they allow has not been analysed |
| `near/intents`, commit `fce0936b1699e0591204ce152a78afc1c1338b35` | `contracts/defuse/src/contract/mod.rs`, `admin_call.rs`, `admin.rs`, `upgrade.rs` read for the roles in section 3 |
| L2BEAT Stage 1 requirements | Read at `forum.l2beat.com/t/the-stages-framework/291` and in `l2beat/l2beat` at commit `d0e66842`, `packages/config/src/common/stages/getRollupStage.ts` |

L2BEAT's Stage 1 requirements for a Security Council, paraphrased from the
forum post (last changelog entry 30 April 2026): the council acts through a
multisig of at least 8 participants with a 75% threshold; participants should
come from different companies and jurisdictions; addresses belonging to one
entity are counted as one; and the participants' identities or pseudonyms are
publicly disclosed. Upgrades started by anyone outside the council must leave
users an exit window of at least 5 days. The site's Stages page
(`l2beat.com/stages`, which redirected to `ethbeat.org/stages` on the retrieval
date) and the source file above still said 7 days. This file uses 5 days, the
most recent published change, and the dashboard shows both.

## Appendix B. Provisional protocol lists

From `api.llama.fi/protocols`, pulled 2026-11-13 04:54 UTC, by the rules in
section 4. Provisional: the frozen list is `data/universe.csv`.

**Near**

| # | Listing | DefiLlama slug | Category | TVL on chain ($M) | Total TVL, all chains ($M) |
|---|---|---|---|---|---|
| 1 | Rhea Lend | `rhea-lend` | Lending | 132.3 | 132.3 |
| 2 | NEAR Intents | `near-intents` | Bridge | 86.2 | 178.7 |
| 3 | Meta Pool Near | `meta-pool-near` | Liquid Staking | 71.6 | 71.6 |
| 4 | RHEA LST | `rhea-lst` | Liquid Staking | 63.0 | 63.0 |
| 5 | NEAR Bridge | `near-bridge` | Canonical Bridge | 43.8 | 105.5 |
| 6 | LiNEAR Protocol | `linear-protocol` | Liquid Staking | 40.9 | 40.9 |
| 7 | Rhea Dex | `rhea-dex` | Dexs | 20.8 | 20.8 |
| 8 | Portal | `portal` | Bridge | 4.1 | 1260.7 |
| 9 | KAIO | `kaio` | RWA | 4.0 | 34.7 |
| 10 | Jumbo Exchange | `jumbo-exchange` | Dexs | 1.0 | 1.0 |
| 11 | HERE Wallet staking | `here-wallet-staking` | Liquid Staking | 0.8 | 0.8 |

**Solana**

| # | Listing | DefiLlama slug | Category | TVL on chain ($M) | Total TVL, all chains ($M) |
|---|---|---|---|---|---|
| 1 | Sanctum Validator LSTs | `sanctum-validator-lsts` | Liquid Staking | 1407.2 | 1407.2 |
| 2 | Kamino Lend | `kamino-lend` | Lending | 1170.0 | 1170.0 |
| 3 | Jupiter Lend | `jupiter-lend` | Lending | 940.6 | 940.6 |
| 4 | Raydium AMM | `raydium-amm` | Dexs | 902.3 | 902.3 |
| 5 | Binance Staked SOL | `binance-staked-sol` | Liquid Staking | 855.2 | 855.2 |
| 6 | Jito Liquid Staking | `jito-liquid-staking` | Liquid Staking | 806.2 | 806.2 |
| 7 | Jupiter Perpetual Exchange | `jupiter-perpetual-exchange` | Derivatives | 601.8 | 601.8 |
| 8 | Jupiter Staked SOL | `jupiter-staked-sol` | Liquid Staking | 400.1 | 400.1 |
| 9 | OnRe | `onre` | RWA | 309.4 | 309.4 |
| 10 | Orca DEX | `orca-dex` | Dexs | 268.9 | 268.9 |

**Sui**

| # | Listing | DefiLlama slug | Category | TVL on chain ($M) | Total TVL, all chains ($M) |
|---|---|---|---|---|---|
| 1 | Suilend | `suilend` | Lending | 125.9 | 125.9 |
| 2 | NAVI Lending | `navi-lending` | Lending | 106.3 | 106.3 |
| 3 | SpringSui | `springsui` | Liquid Staking | 51.5 | 51.5 |
| 4 | Current | `current` | Lending | 50.8 | 50.8 |
| 5 | Ember | `ember` | RWA | 34.5 | 90.0 |
| 6 | Haedal Protocol | `haedal-protocol` | Liquid Staking | 27.9 | 27.9 |
| 7 | Bucket Protocol V2 | `bucket-protocol-v2` | CDP | 24.3 | 24.3 |
| 8 | Cetus CLMM | `cetus-clmm` | Dexs | 23.4 | 23.4 |
| 9 | Volo LST | `volo-lst` | Liquid Staking | 22.0 | 22.0 |
| 10 | Bucket CDP | `bucket-cdp` | CDP | 12.6 | 12.6 |

**Aptos**

| # | Listing | DefiLlama slug | Category | TVL on chain ($M) | Total TVL, all chains ($M) |
|---|---|---|---|---|---|
| 1 | Decibel | `decibel` | Derivatives | 29.3 | 29.3 |
| 2 | KAIO | `kaio` | RWA | 5.7 | 34.7 |
| 3 | Echelon Market | `echelon-market` | Lending | 4.4 | 4.4 |
| 4 | Amnis Finance | `amnis-finance` | Liquid Staking | 2.6 | 2.6 |
| 5 | Propbase | `propbase` | RWA | 1.4 | 1.4 |
| 6 | Thala LSD | `thala-lsd` | Liquid Staking | 1.2 | 1.2 |
| 7 | TruStake | `trustake` | Liquid Staking | 1.1 | 2.4 |
| 8 | Yield AI | `yield-ai` | AI Agents | 1.0 | 1.0 |
| 9 | Hyperion | `hyperion` | Dexs | 1.0 | 1.0 |
| 10 | PancakeSwap AMM | `pancakeswap-amm` | Dexs | 0.9 | 1341.2 |

**Base**

| # | Listing | DefiLlama slug | Category | TVL on chain ($M) | Total TVL, all chains ($M) |
|---|---|---|---|---|---|
| 1 | Morpho Blue | `morpho-blue` | Lending | 4061.0 | 10484.1 |
| 2 | Grove Finance | `grove-finance` | Onchain Capital Allocator | 498.8 | 1107.6 |
| 3 | Aave V3 | `aave-v3` | Lending | 475.9 | 14530.9 |
| 4 | Spark Liquidity Layer | `spark-liquidity-layer` | Onchain Capital Allocator | 368.5 | 2801.0 |
| 5 | Uniswap V3 | `uniswap-v3` | Dexs | 305.8 | 1414.9 |
| 6 | Aero Slipstream | `aero-slipstream` | Dexs | 90.2 | 122.0 |
| 7 | Uniswap V4 | `uniswap-v4` | Dexs | 90.0 | 1116.7 |
| 8 | Aerodrome Slipstream | `aerodrome-slipstream` | Dexs | 72.7 | 72.7 |
| 9 | Uniswap V2 | `uniswap-v2` | Dexs | 70.8 | 786.8 |
| 10 | Aera V3 | `aera-v3` | Onchain Capital Allocator | 60.7 | 165.8 |
