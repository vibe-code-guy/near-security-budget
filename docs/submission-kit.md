# Submission kit

Drafts for the demo post and the demo video. The author posts and submits;
nothing here is sent by a tool. The submission payload itself is not kept in
the repository.

## X post (single post, under 280 characters)

```
Is NEAR safe enough to settle agent money? I fixed 3 tests before pulling the data.

Bounties: holds, with a caveat
Hack losses: fails
Who holds the keys: fails

Built at NEAR HACKATHON. Re-run it yourself: <REPO LINK>

@NEARProtocol #NEARHackathon
```

Attach: the demo video, or `docs/first-screen.png` plus two or three images
from `docs/screens/` (the control section and the timeline read best).
Optional extra tags: @NearLegion @NearBuilders.

## X thread (optional, after the first post)

```
2/ The thesis: NEAR's long-term value rests on being trusted to settle agent money. That trust is measurable as security budget: what is paid to find bugs, and who can change the contracts, relative to the value secured. Peers: Solana, Sui, Aptos, Base.

3/ Bounties: 89.1% of NEAR's top-10 TVL has a live public bounty; the peer median is 41.8%. I expected this to fail. Caveat: the peer bar is zero in two of three size bands, and under a stricter reading the verdict is "can't tell".

4/ Losses: NEAR lost 8.38% of its average TVL per year over 24 months. The peer median is 2.37% to 2.77%. Sui is worse at 9.97%.

5/ Control: read-only view calls on NEAR mainnet show one full-access key on the Sputnik DAO factory can replace the DAO that owns intents.near. That path covers 44.0% of the TVL I assessed. No protocol I assessed enforces an upgrade delay.

6/ What NEAR does here: 54 accounts read by view call (keys, roles, DAO policies), contract source read at named commits, a sourced timeline of the 1 October exploit, and the thesis hash anchored on NEAR before the results were written.

7/ Everything rebuilds with `make all`, no keys. What did I get wrong? Repo: <REPO LINK>
```

## Demo script (2 to 3 minutes)

| Time | On screen | Say |
|---|---|---|
| 0:00 to 0:15 | `site/index.html`, top of page: title and the one-sentence finding | "Agents need somewhere to settle money. Is NEAR safe enough? I fixed three tests before pulling the data, then ran them against Solana, Sui, Aptos and Base." |
| 0:15 to 0:40 | The KPI row, then the verdict strip | Read the three verdicts: "Bounties: holds, with a caveat. Hack losses: fails. Who holds the keys: fails." Point at 8.38%, 89.1%, 1 signer, 0%. |
| 0:40 to 1:05 | Scroll to C2. Hover the NEAR bar and the Sui bar; click the Amount column of the hack table | "NEAR lost 8.38% of its TVL per year. The peer median is under 3%. Sui is worse. These are the 98 hack rows behind it." |
| 1:05 to 1:30 | C1: stacked bars, then the scatter; hover Meta Pool and Uniswap V4 | "I expected NEAR to fail on bounties. It does not: 89% of its top-10 TVL is covered. But the bar is low, and Meta Pool offers $5K against $75M." |
| 1:30 to 2:05 | C3: the matrix, then the control-path diagram; follow the red arrow | "Every upgrade needs three of five council votes. Except one key on the Sputnik factory can replace the DAO itself. That reaches intents.near. And nothing delays an upgrade." |
| 2:05 to 2:25 | Terminal: run the two `curl` view calls from README step 4 | "You can check it yourself with two read-only calls. No account, no keys." |
| 2:25 to 2:45 | Case study timeline | "On 1 October the exploit ran undetected for forty hours. The pause took 29 minutes. The fix took a day and a half." |
| 2:45 to 3:00 | Terminal: `make all`, then the provenance section | "Everything rebuilds from cached data with one command. The claims were hashed, timestamped and anchored on NEAR before the results were written." |

Before recording: use a clean browser profile and a terminal prompt that shows
no account or machine name.
