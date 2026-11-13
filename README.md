# near-security-budget

An investment thesis for NEAR, tested against public data: is the ecosystem's
security budget (bug bounties, incident record, and who controls the contracts)
in line with the value it secures, compared with Solana, Sui, Aptos and Base?

Built at NEAR HACKATHON, track: Investment Thesis (`thesis`).

**Status: stub.** The claims and their kill criteria are registered in
`THESIS.md` before any data is pulled. The pipeline, the dashboard
(`site/index.html`) and the "do X, see Y" steps for judges are added after that.

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
