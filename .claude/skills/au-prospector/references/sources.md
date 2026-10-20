# Data sources

Rule: **free first, paid second**, and pay only for accounts that have earned it. Every paid call goes through `~/.claude/skills/au-prospector/scripts/treg_call.py`.

## Free sources (use your own WebSearch/WebFetch tools)
| Need | Source |
|---|---|
| Is it a real Australian company? Legal name, ABN, state | ABN Lookup: https://abr.business.gov.au/Search/ResultsActive?SearchText=<name> |
| Infrastructure hiring signals | `site:seek.com.au "VMware" engineer Sydney`, `site:seek.com.au "infrastructure engineer" <industry>`, plus LinkedIn job search results |
| Tech clues | Company careers page and job ads (they name the stack), case studies by vendors and MSPs ("<company> migrates to..."), the company's own news |
| Triggers | iTnews, CRN Australia, ARN, AFR, SmartCompany, news search for "<company> cyber incident", "appoints CIO" or "acquires" |
| Growth lists | AFR Fast 100, Deloitte Technology Fast 50 AU, SmartCompany Smart50 |
| Headcount sanity check | The LinkedIn company page (search result snippets often show it) |

## Treg (paid, pay-per-call aggregator)
Use the `mcp__treg__*` MCP tools (`call`, `catalog_get`, `catalog_search`, `balance`). Pass routing options as `headers` (`X-Treg-Route-Max-Cost`, `X-Treg-Route-Waterfall`, `X-Treg-Route-Prefer`, `X-Treg-Route-Exclude`), and always pass an `idempotency_key` on paid calls so retries after a timeout are free. `scripts/treg_call.py` is the fallback when the MCP isn't connected.

Before using an endpoint that isn't listed below, run `catalog_get` on it for params and price. On routed `treg.*` endpoints the result is very large (it lists every provider); save it and query it with jq.

### Confirmed endpoints (tested 2026-10-14)
| Purpose | Endpoint | Key params | Observed cost |
|---|---|---|---|
| **Persona search (LinkedIn-sourced)** | `icypeas.people.search` | body `{"query": {currentJobTitle, currentCompanyWebsite, location, currentCompany.industry, currentCompany.headcount, ...}, "pagination": {"size": N}}`; each filter is `{include:[], exclude:[]}` and headcount is `{">=":, "<=":}` | ~$0.0004/row (7 rows = $0.0027) |
| Size a persona query | `icypeas.people.search.count` | same `query` | free |
| People search, routed fallback | `treg.people.search` | `{"company_domain", "title" (one string), "country", "limit"}`; a `titles` array is **ignored** and returns the whole company | $0.006 for 15 rows |
| Find work email | `treg.people.email.find` | `{"full_name", "domain", "linkedin_url"}`, header Max-Cost 0.25, **no** Verify header (it times out) | $0.005 (served by quickenrich) |
| Verify email | `treg.people.email.verify` | `{"email"}` | $0.0015 (trykitt) |
| Find phone | `treg.people.phone.find` | `{"full_name", "domain", "linkedin_url"}`, Max-Cost 0.50 | free on a miss; AU hit rate low |
| Web search | `treg.web.search` | `{"q": "..."}` (`query` is rejected) | ~$0.00015 |
| Page extract | `treg.web.extract` | `{"url": "..."}` | under $0.001 |

The raw response from `treg.people.email.find` often includes `company_phone`, `revenue` band, `employee_count` and `email_verification_date`, so capture them.

### Known LinkedIn industry labels (for `currentCompany.industry`)
Confirmed: `Hospitals and Health Care`, `Law Practice`. Others to try (validate with the free count first): `Financial Services`, `Insurance`, `Accounting`, `Retail`, `Higher Education`, `Primary and Secondary Education`, `Transportation, Logistics, Supply Chain and Storage`, `Manufacturing`, `Software Development`, `Medical Practices`, `Hospitals`, `Mental Health Care`, `Wholesale`. Add each confirmed label here once it's tested.

### Blocked as of 2026-10-14 (Cloudflare 403 "DNS points to prohibited IP"; free failures)
`apollo.people.search`, `harvestapi.linkedin.leads.search`, `findymail.search.name`, `limadata.*`; `wiza` shows as "account exhausted". ContactOut, Tomba, AI Ark and LeadMagic were intermittently blocked and working again later the same day. These are problems on Treg's side. Retest one occasionally; if Apollo comes back it is free for people search (no contact data) and useful for cross-checking.

### Why not scrape LinkedIn directly (e.g. with Scrapling)
Scrapling is a good general-purpose scraper, but LinkedIn people data sits behind login. Scraping it means running a logged-in account that LinkedIn will restrict or ban, and it breaches LinkedIn's terms. Icypeas via Treg returns the same LinkedIn profile fields (title, start date, profile URL, company size and industry) from a licensed dataset, for fractions of a cent and with no account risk. Scrapling is still worth using for **company websites, careers pages and Seek job ads** if `treg.web.extract` gets blocked on a site.


### Lessons from run 2026-10-14 (40 healthcare accounts NSW/VIC, 54 contacts, US$9.02)
- **Email:** `treg.people.email.find` hit 51/54. Trykitt usually serves it and returns SMTP validity inline, so a separate verify is only needed for other providers. Mimecast/Proofpoint domains come back `valid-risky`.
- **Mobile, primary:** `prospeo.people.phone.find` with body `{"only_verified_email": false, "enrich_mobile": true, "only_verified_mobile": true, "data": {"linkedin_url": ...}}`. It hit 30/54 at $0.245 per hit (misses free), every one a verified +61 mobile, and it also BounceBan-verifies the email, upgrading most `valid-risky` addresses to valid. Check `job_history`: it exposes stale LinkedIn titles.
- **Mobile, fallback:** `treg.people.phone.find` with `X-Treg-Route-Exclude: aviato,limadata,leadsforge,prospeo,quickenrich` and `X-Treg-Route-Verify: true`. Tomba and ContactOut returned good AU numbers; **QuickEnrich, FindyMail, LeadMagic and AI Ark returned US/UAE/Irish numbers for AU people**. Discard any non-+61 number.
- **HLR check:** `hlrlookup.people.phone.verify` body `{"telephone_number": "614xxxxxxxx", "save_to_cache": "PRIVATE", "cache_days_global": 0, "cache_days_private": 0}` (no "+"), $0.0066. Telstra often returns NOT_AVAILABLE_NETWORK_ONLY rather than LIVE.
- **Domain gotcha:** LinkedIn company websites can be wrong (the marketing domain differs from the mail domain, e.g. a `.com` site but a `.com.au` or `.org.au` mail domain). The phone provider's `company.domain` is more reliable.
- **Headcount gotcha:** LinkedIn headcount badly understates frontline-heavy healthcare orgs (one group showed ~1,600 on LinkedIn vs ~5,500 actual). Check the company description.

### Lessons from run 2026-10-14 #2 (40 financial services accounts, 94 contacts, US$7.60)
- **One call for every CFO/CRO:** `icypeas.people.search` accepts a list in `currentCompanyWebsite.include`, so one call with all 40 domains returned 87 CFO/CRO/COO rows for $0.03. Do this instead of one call per account.
- **Prospeo rate-limits hard** (HTTP 429, free) on Treg's shared account after a few calls in a row. Send it one at a time. If it keeps returning 429, switch to the routed fallback rather than waiting.
- **Routed fallback quality for AU mobiles:** Tomba and ContactOut were mostly right and HLR-live. FindyMail was mixed (some AU-live, some 1800/landlines, one Hong Kong). AI Ark and LeadMagic returned several foreign numbers (+1, +44, +65, +353). Always keep `X-Treg-Route-Verify: true` and discard non-+61 results. ContactOut costs $0.25 per hit.
- **Prospeo `job_postings`** in the company block shows live hiring. Look for risk/resilience/infra roles as triggers (e.g. an insurer hiring an Operational Risk Manager).
- **Stale-person check:** when the email finder only returns an address at a *different* company's domain, the person has probably left (e.g. an IT Ops Manager who has since moved to another firm).
- **Email domains differ from the website** for several FS firms: the corporate `.com` resolves to a `.com.au` mail domain, and some use a `.net.au` mail domain against a `.com.au` website. Always confirm the mail domain.

### Lessons from run 2026-10-14 #3 (38 allied-health accounts, 62 contacts, US$5.96)
- **Allied health groups rarely have IT staff on LinkedIn.** An IT-title-only sweep found 22 people across NSW+VIC. Sweep by `currentCompanyName` keywords (Physio, Dental, Rehab, Psych, Therapy, Hearing, Optometr...) and by LinkedIn industry (Medical Practices, Wellness and Fitness Services, Mental Health Care, Individual and Family Services), and include CFO/COO/CEO/MD titles. Expect noise from gyms, supplement brands and family services, so curate by hand.
- **Ownership check via email domain:** if a contact's address is at a parent brand, the company is a tier-1 subsidiary. Drop it.
- **Big physio/podiatry roll-ups are often HQ'd interstate** (e.g. in Brisbane), so they fall outside NSW/VIC runs — park them for a QLD run.
- Routed phone with Prospeo *included* (exclude `aiark,leadmagic,aviato,limadata,leadsforge,quickenrich`) worked well: Tomba first, then FindyMail, Prospeo, ContactOut. Still discard non-+61 results (US, DE numbers seen).

## Cost discipline
- Default per-call ceiling is US$0.50 and default run budget is US$10 (premium setup). The user can change either.
- Re-running enrichment on a known domain or person still costs money, so check `accounts.csv` and `contacts.csv` first.
- Measure spend as the starting `mcp__treg__balance` minus the ending balance.
- Failed calls are free. Empty results are not, so don't retry the same query.
- Only find contact details for Tier A/B accounts.
