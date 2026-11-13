# near-security-budget

An investment thesis for NEAR, tested against public data: is the ecosystem's
security budget (bug bounties, incident record, and who controls the contracts)
in line with the value it secures, compared with Solana, Sui, Aptos and Base?

Built at NEAR HACKATHON, track: Investment Thesis (`thesis`).

**Status: stub.** The claims and their kill criteria are registered in
`THESIS.md` before any data is pulled. The pipeline, the dashboard
(`site/index.html`) and the "do X, see Y" steps for judges are added after that.

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
about two minutes before the first pull) and the git history.

Read the anchor back (view call, no account needed):

```
near contract call-function as-read-only social.near get json-args '{"keys":["near-thesis.near/near-security-budget/**"]}' network-config mainnet now
```

It returns the commit id and the SHA-256 in the first row.

Check the registered text and its timestamp:

1. `git show f84b548:THESIS.md | sha256sum` prints the hash above, and
   `registration/THESIS.f84b548.md` is the same bytes.
2. `pip install opentimestamps-client`, then
   `ots verify registration/THESIS.f84b548.md.ots` (needs a Bitcoin node), or
   drop the `.md` and `.ots` files on https://opentimestamps.org. The proof was
   submitted to four public calendar servers and has since been upgraded, so it
   carries Bitcoin block attestations.

Commit dates are set by the author's machine, so they are evidence of order,
not proof. The timestamp proof is the independent check.

## Ground rules

- Read-only. No keys, no transactions, no testing of any vulnerability, nothing
  sent to any contract. Only published bounty terms, public source code and
  public chain state are analysed.
- No number is invented. Where something cannot be computed, `THESIS.md` says so.

## How this was built

Claude Code (Anthropic's coding agent) wrote the code and drafted the documents
in this repository under the author's direction. The author chose the thesis,
approved the claims and kill criteria, and filled the bounty table by hand.
Commits carry no co-author line, so this section is the disclosure.

## License

MIT, see `LICENSE`.
