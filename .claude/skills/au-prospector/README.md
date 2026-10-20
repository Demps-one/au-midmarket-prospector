# au-prospector

A Claude Code skill that works as an SDR for a managed hosting provider's Australian launch. It finds mid-market AU companies that fit the provider's ICP and maps their IT and finance decision-makers from LinkedIn-sourced data via Treg. It then finds verified emails and AU mobiles, scores each account, and writes deduplicated CSVs plus a call sheet for each run.

`SKILL.md` is the entry point Claude reads. `references/` holds the ICP, personas, data sources and per-run lessons. `scripts/` holds the CSV merge, call-sheet builder and a raw Treg client.

## Set up on a new machine

The repo is `github.com/Demps-one/au-midmarket-prospector`. The skill sits at `.claude/skills/au-prospector/` inside it.

1. Clone the repo, then link the skill into Claude Code's skills folder:
   ```
   gh repo clone Demps-one/au-midmarket-prospector ~/au-midmarket-prospector
   ln -s ~/au-midmarket-prospector/.claude/skills/au-prospector ~/.claude/skills/au-prospector
   ln -s ~/au-midmarket-prospector/.claude/skills/security-review ~/.claude/skills/security-review
   git -C ~/au-midmarket-prospector config core.hooksPath .githooks   # turns on the commit safety check
   ```
   (Windows: open Claude Code inside the cloned folder and it picks the skill up as a project skill.)
2. Connect Treg as an MCP server with your Treg API token. **The token is never stored in this repo.**
   ```
   claude mcp add --transport http --scope user treg https://treg.to/mcp/ --header "Authorization: Bearer ***"
   ```
   Alternatively, `export TREG_TOKEN=...` and the skill falls back to `scripts/treg_call.py`.
3. Data folder: scripts use `$PROSPECT_DATA_DIR`, else `data/` at the repo root, else `~/prospecting/au/`.
4. Phone: open the repo in Claude Code on the web (in the Claude app). The skill loads as a project skill; Treg must be connected in that environment too.
5. Keep machines in sync: `git pull` before a run, then commit and push after one.

## Data and privacy

The prospect lists hold names, work emails and mobile numbers of real people, so they are personal information under the Privacy Act 1988. Right now they are **not** in this repo; they stay on the PC where they were created (`~/prospecting/au/`). To share them across devices, move them into `data/` and remove `data/` from the root `.gitignore`. Only do that while the repo is **private**. Cold email must meet the Spam Act 2003 inferred-consent test (see `SKILL.md`).

## Run history

| Date | Run | Accounts | Contacts | Spend (US$) | Call sheet |
|---|---|---|---|---|---|
| 2026-10-14 | Healthcare (hospitals, aged care, diagnostics), NSW+VIC | 40 | 54 | 9.02 | `call-sheet-healthcare-nsw-vic-2026-10-14.csv` |
| 2026-10-14 | Non-bank financial services (mid-market only), NSW+VIC | 40 | 94 | 7.60 | `call-sheet-finserv-nsw-vic-2026-10-14.csv` |
| 2026-10-14 | Allied health (physio, dental, rehab, mental health, vision), NSW+VIC | 38 | 62 | 5.96 | `call-sheet-alliedhealth-nsw-vic-2026-10-14.csv` |

Master totals after these runs: 118 accounts and 210 contacts.

### Ideas for next runs
- A QLD one-off covering the largest physio/allied-health roll-ups headquartered in Brisbane.
- A dedicated phone-enrichment pass for the allied-health contacts still missing a mobile (see `phone` blanks in the allied-health call sheet).
- Other priority verticals from `references/icp-scoring.md` not yet covered: legal, logistics, education, SaaS.
- ABNs are blank on all accounts so far. Fill them from ABN Lookup (free) when there's time.
