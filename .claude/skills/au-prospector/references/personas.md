# Target personas

> **This file is a worked example**, driven by [`use-case.md`](use-case.md). The personas below
> suit the managed-hosting example (IT and finance buyers). Replace them with the job titles that
> matter for your business, or ask Claude to rebuild this file from your `use-case.md` answers.

Only these people go in `contacts.csv`. Everyone else at the account is noise: don't pay to enrich them.

| Persona | Role in the deal | Titles to include (Icypeas `currentJobTitle.include`) |
|---|---|---|
| **P1 · IT lead** | Feels the pain; runs the servers, VMware and backups; first call | `IT Manager`, `Head of IT`, `Head of Information Technology`, `Infrastructure Manager`, `Head of Infrastructure`, `IT Infrastructure`, `IT Operations Manager`, `Head of Technology`, `Technology Manager`, `Systems Manager`, `Cloud Infrastructure` |
| **P2 · IT executive** | Owns the budget and the strategy | `Chief Information Officer`, `CIO`, `IT Director`, `Director of IT`, `Director of Technology`, `Technology Director`, `General Manager IT`, `GM Technology`, `Chief Technology Officer`, `CTO`, `Chief Digital Officer` |
| **P3 · Finance/ops executive** | Economic buyer; signs multi-year hosting contracts | `Chief Financial Officer`, `CFO`, `Finance Director`, `Chief Operating Officer`, `COO` |

**Exclude list** (always send as `currentJobTitle.exclude`). Icypeas matches titles fuzzily, so "Infrastructure" also catches *"Partner – Property, Projects and Infrastructure"* at a law firm:
`Partner`, `Counsel`, `Lawyer`, `Solicitor`, `Associate`, `Property`, `Recruit`, `Talent`, `Assistant`, `Coordinator`, `Intern`, `Graduate`, `Student`, `Sales`, `Account Manager`, `Business Development`, `Project Manager`, `Consultant`, `Former`

## Who to pick per account (max 3 contacts)

- **< 250 staff:** P1 + P3. A CIO is rare at this size, and the CFO usually signs the infrastructure contract.
- **250–1,000 staff:** P1 + P2, plus P3 only on Tier A accounts.
- If several people match one persona, take the most senior. On a tie, take whoever has been **longest in role**, unless someone started in the last 12 months (see below).
- `CTO` at a software/SaaS company is a product-engineering role, which is still relevant for vertical 7 (AU hosting for SaaS). At a non-software company, treat a CTO as P2.

## In-role date is a trigger

Icypeas returns `lastJobStartDate` (MM-YYYY). Store it as `in_role_since`. A **P1 or P2 who started in the last 12 months** is a "new IT leader" trigger in the scoring rubric: new leaders review incumbent providers in their first year. Record it in `triggers`, with the LinkedIn URL as the source.

## Field mapping (Icypeas lead → contacts.csv)

| Icypeas | contacts.csv |
|---|---|
| `firstname` + `lastname` | `full_name` (skip rows where the surname is just an initial, e.g. "Ben H.", because email finders can't resolve them) |
| `lastJobTitle` | `title` |
| (from the table above) | `persona` (P1/P2/P3) |
| `lastJobStartDate` | `in_role_since` |
| `profileUrl` | `linkedin_url` |
| `address` | `location` |
| `lastCompanyWebsite` | `domain` (normalise it) |
| `lastCompanySize` | cross-check against `accounts.employees` |
