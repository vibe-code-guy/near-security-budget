# C3 control trace: working notes (unfinished)

Status: chain state read for all seven protocols by view calls on 2026-11-13
(NEAR mainnet, blocks 224,332,482 to 224,332,753, via free.rpc.fastnear.com).
Source reading is done only for `intents.near`, its controller and the Sputnik
DAO update path. No verdict is drawn here. Nothing below is cached in
`data/raw/near/` yet: `data/c3_targets.json` still has to be written so that
`make data` re-reads every call with block heights.

## Contracts and owners (view calls)

| Listing | Contract | Keys on contract | Owner / top role | Other roles seen |
|---|---|---|---|---|
| NEAR Intents | `intents.near` | 9 function-call (`execute_intents`), 0 full-access | DAO role: `intents.sputnik-dao.near` | Upgrader: `ctl-intents.near`; 7 PauseManagers; no `up_get_delay_status` |
| Rhea Lend | `contract.main.burrow.near` | none | `get_config.owner_id` = `burrow.sputnik-dao.near` | guardians `nicktrust.near`, `doublerose.near` |
| Meta Pool Near | `meta-pool.near` | none | `get_owner_id` = `stnear.sputnik-dao.near` | operator `operator.meta-pool.near` (1 full-access key) |
| RHEA LST | `lst.rhealab.near` | none | super-admin and DAO role: `ref-finance.sputnik-dao.near`; `get_owner_id` = `rhealab.near` | UpgradableCodeStager: `bim.near`, `refchef.near`; UpgradableCodeDeployer: the DAO; `up_get_delay_status.staging_duration` = null |
| NEAR Bridge | `omni.bridge.near` | none | super-admin `rainbowbridge.sputnik-dao.near`; DAO role: that DAO and `omni.bridge.near` itself | UpgradableCodeStager: `bridge-ops.near` (5 full-access keys); UpgradableCodeDeployer: no grantee; `staging_duration` = null |
| LiNEAR Protocol | `linear-protocol.near` | none | `get_owner_id` = `linear.sputnik-dao.near` | managers `owner.linear-protocol.near`, `manager.linear-protocol.near` |
| Rhea Dex | `v2.ref-finance.near`, `dclv2.ref-labs.near` | none | owner `ref-finance.sputnik-dao.near` | guardians / operators `bim.near`, `doublerose.near` |

## Sputnik DAOs in the control paths (`get_policy`, `get_factory_info`, `view_account`)

| DAO | Council | Threshold | Code | `auto_update` |
|---|---|---|---|---|
| `intents.sputnik-dao.near` | 5 implicit accounts, 1 full-access key each | 3 | hash `4zSoHk...` (factory metadata: v3.1, commit `3d568f95`) | true |
| `burrow.sputnik-dao.near` | 5 named accounts | default 1/2 of 5 (3 by the Sputnik formula, to confirm in `policy.rs`) | `4zSoHk...` | false |
| `stnear.sputnik-dao.near` | 4 (one is `n1-gov.sputnik-dao.near`, a DAO) | default 55/100 of 4 (3, to confirm) | global contract `DtHZA1...` (factory metadata: v3.2, commit `2b0f34a3`) | true |
| `ref-finance.sputnik-dao.near` | 5 named accounts | default 1/2 of 5 (3, to confirm) | `4zSoHk...` | false |
| `rainbowbridge.sputnik-dao.near` | 5 implicit accounts | 2/5 ratio of 5 (3, to confirm) | hash `8RMeZ5...` (factory metadata: v2.0, commit `c2cf1553`); no `get_factory_info` method | not applicable (to confirm in v2 source) |
| `linear.sputnik-dao.near` | 5 (one is `hos-root.sputnik-dao.near`, a DAO) | default 1/2 of 5 (3, to confirm) | `4zSoHk...` | true |

## Sputnik factory `sputnik-dao.near`

- `view_access_key_list`: 3 full-access keys. `get_owner` = `sputnik-dao.near` (itself).
- `get_default_version` = [3, 2]; `get_contracts_metadata` maps the code hashes above to commits.
- Source, `sputnikdao2/src/upgrade.rs` at commits `3d568f95` (v3.1) and `2b0f34a3` (v3.2):
  `update()` accepts a call whose predecessor is the factory when `auto_update` is true,
  takes the new code from the call input and deploys it, with no proposal. The source
  comment describes this as by design.
- On `main` (commit `5434a59d`), `update()` adds a two-week proposal gate for factory
  auto-updates. That is PR #233, merged 2026-03-24. None of the six DAOs above runs a
  code hash newer than v3.2 (commit dated 2026-02-25), so the gate is not deployed on them.
- Consequence to carry into C3a, pending a careful re-read: for the three DAOs with
  `auto_update: true` (behind NEAR Intents, Meta Pool and LiNEAR), one full-access key on
  the factory account is enough to replace the DAO's code. This confirms the public claim
  by Docket (https://github.com/aditi3175/docket) for Meta Pool and LiNEAR and extends it to
  `intents.sputnik-dao.near`. The mapping from code hash to commit is the factory's own
  metadata; it was not rebuilt.

## `ctl-intents.near` (Upgrader on `intents.near`)

- `contract_source_metadata`: aurora-is-near/aurora-controller-factory, version 0.3.3. No keys on the account.
- Roles on chain: DAO = `intents.sputnik-dao.near`; Updater = 1 implicit account (1 key);
  Downgrader = 2 implicit accounts (1 key each); Releaser, Deployer, Pauser, Unpauser = none.
- Source at tag 0.3.3 (`contract/src/lib.rs`) and README: `add_release_info` is DAO only;
  `upgrade` (DAO or Updater) deploys a registered release and requires a higher version than
  the deployed one; `unrestricted_upgrade` and `delegate_execution` are DAO only; `downgrade`
  (DAO or Downgrader) deploys the registered downgrade hash.
- So the single Updater key can move `intents.near` only to code the DAO has registered.

## Still to do

- Read the upgrade gating in source for Rhea Lend, Meta Pool, RHEA LST, NEAR Bridge, LiNEAR, Rhea Dex.
- Confirm the Sputnik threshold formula in `policy.rs`; check v2.0 DAO code for a factory path.
- Count keys of every council member; `doublerose.near` has more than 100 keys (needs a paginated call).
- Write `data/c3_targets.json`, cache the calls with `make data`, write `pipeline/c3.py` and the C3a / C3b tests.
- L2BEAT Stage 1 comparison column.
