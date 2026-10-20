# ICP and scoring

> **This file is a worked example** (a managed hosting provider entering Australia), driven by
> [`use-case.md`](use-case.md). Edit it to match your business, or fill in `use-case.md` and ask
> Claude to rebuild this file from your answers.

## Ideal customer profile (draft — refine for your business)
- **Geography:** HQ in Australia, or an Australian entity that makes its own IT decisions. Priority: NSW and VIC (near the Sydney/Melbourne data centres), then QLD, WA, SA.
- **Size (mid-market):** ~100–1,000 employees, roughly A$20m–A$500m revenue. 50–100 staff is acceptable with strong signals.
- **Infrastructure:** runs meaningful IT itself — on-prem servers, colocation, VMware, legacy hosting, or a public cloud estate it struggles to manage.
- **IT team:** small to mid-sized (roughly 2–20 people), so 24/7 managed support has real value.

### Priority verticals (data-sensitive or uptime-sensitive)
1. Healthcare — private hospitals, day surgeries, clinic groups, aged care, allied health, pathology/radiology
2. Financial services outside the big banks — wealth, super admin, insurance brokers, lenders, fintech
3. Professional services — law firms, accounting and engineering firms
4. eCommerce and retail — online-heavy retailers with peak-season load
5. Education — independent schools, RTOs, private colleges
6. Logistics, manufacturing and distribution with ERP/WMS on-prem
7. Software/SaaS vendors serving regulated Australian customers who need AU hosting

### Mid-market guardrails (BDM instruction, 2026-10-14)
The provider sells to the mid-market. Tier-1 organisations build this capability in-house and are not targets.
- Exclude: the big-4 banks and other major banks, major insurers, mega industry super funds, ASX 200 companies, and **subsidiaries of any of these** (their IT decisions sit at group level).
- **IT team-size check:** run a free `icypeas.people.search.count` with `currentCompanyWebsite` = the domain and infra/ops titles (`Information Technology, IT, Infrastructure, Systems Engineer, Systems Administrator, Network Engineer, Service Desk, Cloud, DevOps, Platform Engineer, Technology Operations, Security Engineer`). More than ~40 means they run it in-house: drop them.
- Overseas-HQ subsidiaries usually have IT run globally: drop them unless the AU entity clearly decides for itself.

### Exclude or flag
- Federal/state government agencies (long procurement and IRAP requirements; the provider's IRAP status is unknown) → exclude unless the user asks
- Enterprises above ~2,000 staff → exclude (they usually build their own capability)
- Hosting providers and data centre operators → competitors, exclude
- MSPs, IT consultancies and system integrators → put in `partners.csv`, not `accounts.csv`
- Fully cloud-native startups with a strong DevOps team → low fit unless they show cloud-cost pain

## Scoring rubric (0–100)

| Dimension | Points | How to score |
|---|---|---|
| Firmographic fit | 0–30 | Size in band (15), priority vertical (10), NSW/VIC HQ (5) |
| Infrastructure fit | 0–30 | Evidence of on-prem/VMware/colo/legacy hosting (15), data-sovereignty or compliance obligation (10), small IT team (5) |
| Timing triggers | 0–30 | Each **dated** trigger in the last 12 months scores 10, max 30: infra job ad, new IT leader (incl. a P1/P2 whose `in_role_since` is within 12 months), M&A, breach or cyber incident, rapid growth/funding, VMware/Broadcom pain, hardware refresh, office or data centre move, cloud-cost complaint |
| Reachability | 0–10 | Named P1 or P2 persona found (5), `valid` email or direct phone for them (5) |

**Tiers:** A ≥ 70 (call this week) · B 50–69 (nurture or sequence) · C < 50 (park)

Score from evidence only. A dimension with no evidence scores 0. Don't award points for "probably".

## accounts.csv columns
`company, domain, abn, hq_state, industry, employees, revenue_aud_est, score, tier, why_fit, infra_signals, triggers, trigger_dates, found_via, source_urls, date_added, status`

- `infra_signals`, `triggers` and `source_urls`: separate multiple values with semicolons.
- `status`: starts as `new`. The BDM updates it to `contacted`, `meeting`, `disqualified`, and so on. Never overwrite a status the BDM has changed.

## contacts.csv columns
`domain, company, full_name, title, persona, in_role_since, location, linkedin_url, email, email_verdict, email_unverified, phone, phone_verdict, contact_source, date_added`

- `persona`: P1 / P2 / P3 (see `personas.md`).
- `email_verdict`: `valid` / `risky` / blank. `phone_verdict`: `direct` / `mobile` / `switchboard`.
- `contact_source`: the provider chain, e.g. `icypeas→quickenrich→trykitt(valid-risky, mimecast)`.

## partners.csv columns
`company, domain, hq_state, type, notes, source_urls, date_added`
