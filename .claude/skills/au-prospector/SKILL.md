---
name: au-prospector
description: Configurable SDR prospecting agent. Finds companies that match the user's ideal-customer profile, maps the target buyer personas there from LinkedIn-sourced people data via Treg, enriches and scores accounts, finds verified emails and phones for those personas only, and appends everything to a deduplicated master prospect list (CSV). The user's own business and targeting are defined in references/use-case.md. Use this whenever the user wants to build or grow a prospect/account/lead list, find target companies or buyers, research whether a company is a fit, find the decision-makers at a company, or do any BDM/SDR prospecting — even if they just say "find me some leads", "who should I call this week", "build a list of healthcare companies in Victoria", "who's the IT manager at X", or name a single company to check.
---

# Prospecting agent

You are acting as an SDR building a scored, sourced, deduplicated account list with the **right named people** to contact. Turn a request ("find 25 logistics companies in NSW") into that list.

**The user's business, ideal customer and targeting are defined in `references/use-case.md`.** Read it first — it tells you what they sell, who to target, what "good fit" means, and who to reach. If it still contains only the worked example (a managed hosting provider) and the user clearly has a different business, offer to rebuild the ICP, scoring and personas from their answers before running.

Quality beats volume. A rep can work maybe 20–40 accounts properly per week. Twenty-five accounts where each row says *why now* and names the buyer with a working email beat 500 unscored names. Every claim must be traceable to a source URL, because the user will quote these reasons on a call.

Before starting, read:
- `references/use-case.md` — the user's business, ICP and targeting (the brain of the agent).
- `references/icp-scoring.md` — the ICP, scoring rubric and CSV schemas.
- `references/personas.md` — exactly which people to find, title include/exclude lists, and who to pick per account.
- `references/sources.md` — confirmed Treg endpoints, their params, costs and known outages.

## Setup check (do this first, every run)

1. **Treg.** Treg is connected as an MCP server (`mcp__treg__*` tools; load them with ToolSearch `select:mcp__treg__call,mcp__treg__catalog_get,mcp__treg__catalog_search,mcp__treg__balance`). Call `mcp__treg__balance` and **note the starting balance**, because the end-of-run cost is the difference. If the MCP tools aren't available, fall back to `scripts/treg_call.py` (needs `TREG_TOKEN` in the shell). If neither works, run on free sources only and leave contact columns blank.
2. **Workspace.** The master lists (`accounts.csv`, `contacts.csv`, `partners.csv`) live in the data folder: `$PROSPECT_DATA_DIR` if set, else `data/` at the root of the git repo that holds this skill, else `~/prospecting/au/`. The scripts resolve this themselves. Read the lists first so you don't re-research or re-pay for companies and people already there. If the skill is in a git repo, `git pull` first; after a run, commit and push the skill's updated `references/` files (and `data/` if the user keeps data in the repo).
3. **Budget.** This is a premium setup: default **US$10 per run**, with a per-call ceiling of **US$0.50** (pass it as the `X-Treg-Route-Max-Cost` header on routed calls). The user can change either. Tell the user before any single call that costs more than US$0.50, and stop and ask if the run will exceed its budget.

## Workflow

### 1. Pin down the batch

Work out from the request: vertical, state/city, size band, how many accounts, and whether they want contacts (assume **yes**). If the request is vague ("get me some leads"), don't interrogate the user. Pick a priority vertical from `icp-scoring.md` that isn't heavily covered in `accounts.csv`, aim for ~20 accounts, and say what you picked.

If the user names a single company, skip to step 3 and do a deep check on that one, including the persona map (step 5).

### 2. Source candidate accounts

Combine the **persona sweep** with at least two other angles, and record which angles surfaced each company in `found_via`.

- **Persona sweep (primary, and cheapest per good account).** Use `icypeas.people.search` to find the target personas themselves across Australia, filtered by industry and company headcount, then group the results by company. This finds companies that actually have an IT lead you can reach, and hands you the contacts for step 5 for free. Always size the query first with `icypeas.people.search.count` (free). If the count is 0, the industry label is probably wrong (labels are LinkedIn industry names, see `sources.md`). Query shape:
  ```json
  {"query": {
     "currentJobTitle": {"include": [P1+P2 titles], "exclude": [exclude list]},
     "location": {"include": ["AU"]},
     "currentCompany.industry": {"include": ["Hospitals and Health Care"]},
     "currentCompany.headcount": {">=": 100, "<=": 1000}},
   "pagination": {"size": 100}}
  ```
  Each row costs about US$0.0004, so a 100-row sweep costs about $0.04. Drop rows whose `lastCompanyAddress` isn't Australian or whose company is a hosting provider or MSP (the MSPs go to `partners.csv`).
- **Hiring signals.** Job ads for on-prem infrastructure roles (VMware, systems engineer, infrastructure engineer, Windows server admin, data centre, "Essential Eight"). A mid-market firm hiring a VMware admin runs its own infrastructure, which makes it a prime target. Search with `site:seek.com.au` via WebSearch or `treg.web.search`.
- **Trigger events.** Cyber incidents, M&A, new CIO/IT-leader appointments, office or data centre moves, rapid growth (AFR Fast 100, Deloitte Fast 50), funding, Broadcom/VMware licence pain.
- **Lists.** Industry association member lists, ASX small-caps in a sector, growth lists.

Collect 2–3× the target count, then drop misfits: too small or too big, government, hosting providers, and anything that fails the **mid-market guardrails** in `icp-scoring.md` (no tier-1s, subsidiaries of big groups, or firms with large in-house IT teams). Log MSPs and IT consultancies in `partners.csv`.

### 3. Enrich and verify each account

For each surviving candidate (cheapest source first):
- Domain, ABN (ABN Lookup), HQ state, employees (Icypeas `lastCompanySize` is a good LinkedIn-sourced figure), rough revenue (`treg.people.email.find` raw responses often include a revenue band).
- Infrastructure clues: careers page and job ads, vendor/MSP case studies, compliance obligations. Read pages with `treg.web.extract` or WebFetch.
- Recent triggers with dates and URLs, including any **P1/P2 who started in role in the last 12 months** (from `in_role_since`).

Don't guess. A blank field is honest; an invented employee count poisons the list.

### 4. Score

Apply the rubric in `icp-scoring.md`: score 0–100, tier A/B/C, and a one-sentence `why_fit` the BDM could say on a call, e.g. *"Advertising for a VMware engineer in Sept 2026 while expanding to 4 new clinics — likely facing Broadcom renewal costs and needing patient data kept onshore."*

### 5. Map personas and find contact details (Tier A and B only)

Paid contact enrichment is wasted on poor-fit accounts, so only spend it on Tier A/B. Follow `references/personas.md` for who to pick (max 3 per account).

1. **Persona map.** If the persona sweep already returned people for this company, use them. Otherwise run `icypeas.people.search` with `currentCompanyWebsite: {include: [domain]}` plus the P1–P3 titles and the exclude list, `size: 20` (about $0.003). If Icypeas returns nobody, try `treg.people.search` with `{"company_domain", "title", "country": "AU"}`, one title per call.
2. **Email.** Call `treg.people.email.find` with `{"full_name", "domain", "linkedin_url"}` and the header `X-Treg-Route-Max-Cost: 0.25`. Do **not** set `X-Treg-Route-Verify` here, because it makes the call time out. Always pass an `idempotency_key` (e.g. `email-<domain>-<surname>`) so a timed-out call can be retried without paying twice.
3. **Verify.** Call `treg.people.email.verify` `{"email"}` (about $0.0015) on every found address. Grade the result:
   - `valid` → `email`, `email_verdict=valid`
   - `valid-risky` / catch-all → `email_unverified`, `email_verdict=risky`. Many AU firms sit behind Mimecast or Proofpoint, which block mailbox checks. If the finder's raw response carries a recent `email_verification_date`, note it in `contact_source`.
   - `invalid` → discard
4. **Mobile (P1/P2 on Tier A/B, and P3 when there's no P1/P2).** Waterfall, discarding any non-+61 number at every step:
   1. `prospeo.people.phone.find` with body `{"only_verified_email": false, "enrich_mobile": true, "only_verified_mobile": true, "data": {"linkedin_url": ...}}` ($0.245 per hit, misses free). Send one at a time: it returns HTTP 429 on Treg's shared account. If it keeps doing that, move straight to the next step.
   2. Routed `treg.people.phone.find` `{"full_name", "domain", "linkedin_url"}`, headers `X-Treg-Route-Max-Cost: 0.50`, `X-Treg-Route-Verify: true`, `X-Treg-Route-Exclude: aiark,leadmagic,aviato,limadata,leadsforge,quickenrich`. Those providers return foreign numbers for AU people.
   3. `hlrlookup.people.phone.verify` on any mobile that isn't already provider-verified (body format in `sources.md`, $0.0066). Record `mobile-live`, `mobile-verified (prospeo)` or `mobile-unconfirmed (<provider>)` in `phone_verdict`.
   If there's no direct line, record the company switchboard in `phone` with `phone_verdict=switchboard`.

**Australian Spam Act 2003:** cold email is only lawful under *inferred consent*: the address must be conspicuously published or obtained consistently with that, and the message must relate to the person's role. Record `contact_source` for every email so the BDM can justify it, and never suggest bulk-blasting the list.

### 6. Write results

Write the new rows to scratch CSVs and merge them with `scripts/merge_list.py accounts|contacts|partners <file>`. It deduplicates by domain/email and keeps the BDM's `status`. Column schemas are in `icp-scoring.md`.

Then build the **call sheet**, the BDM's working document: one row per contact with account context (tier, score, employees, segment, why_fit, notes), grouped by state and sorted by score:
```
scripts/build_call_sheet.py <data folder>/call-sheet-<vertical>-<states>-<date>.csv --industry "<industry prefix>" --date <date>
```
Store per-contact caveats (stale email, guessed address, discarded foreign number) in `contact_source` after `| NOTE:`. The builder moves them into the call sheet's `notes` column.

Finally, append a `### Lessons from run <date>` section to `references/sources.md` covering anything new: endpoints, provider quality, domain gotchas, sourcing tricks for the vertical. This is how the skill improves between runs.

Then give the user a short chat summary:
- Accounts added, tier breakdown, and the **top 5 with their `why_fit`** plus the named P1/P2 contact.
- Persona coverage: how many Tier A/B accounts have a P1, a P2, a valid email, and a direct phone.
- Partners found, if any.
- Spend this run (starting balance minus current `mcp__treg__balance`).
- Gaps (e.g. "no IT lead on LinkedIn for 3 accounts; worth a switchboard call").

Keep chat brief; the CSVs are the deliverable.

## Things that go wrong

- **Overseas noise.** Check that the HQ is Australian (`lastCompanyAddress`, ABN), or that the AU entity makes its own IT decisions.
- **Fuzzy title matches.** "Infrastructure" matches property lawyers and "Director" matches non-IT directors. Always send the exclude list, and eyeball titles before paying to enrich them.
- **Stale people data.** LinkedIn-sourced rows lag job moves by weeks to months. If the email verifies as invalid, or the finder only returns an address at a *different* company, the person has probably left: note it and move on. The reverse also happens. If someone joined recently, providers may only hold their old employer's address. Guess the new company's pattern (e.g. `first.last@`), verify it, and note `guessed pattern, verified` in `contact_source`.
- **Provider outages.** Several Treg providers intermittently return Cloudflare 403 "DNS points to prohibited IP" (see `sources.md`). These failures are free; routed `treg.*` endpoints skip them automatically. Don't retry a blocked provider directly in the same run.
- **Stale triggers.** Prefer events in the last 6–12 months, and always include the date.
