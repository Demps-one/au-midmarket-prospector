# Your use case — fill this in before the first run

This file is the **brain of the agent**. The prospecting skill reads it to understand
what you sell, who you're trying to reach, and what makes a company worth a call.
Everything downstream — the ICP, the scoring rubric, the personas, the talk tracks —
is derived from your answers here.

**How to use it:** answer the questions below in your own words, then either edit
`icp-scoring.md` and `personas.md` to match, or just ask the agent *"read my use-case
file and rebuild the ICP, scoring and personas to fit it."* It will.

A completed example (a managed hosting provider entering Australia) is included at the
bottom so you can see the level of detail that works well. Delete it once you've written
your own, or keep it for reference.

---

## 1. What do you sell?
- **Product / service in one sentence:**
  _What is it, plainly?_
- **The 3–4 things that make a buyer switch to you:**
  _Your real differentiators — price model, speed, support, compliance, a feature nobody else has._
- **Pricing / commercial model:**
  _One-off, subscription, usage-based, multi-year contract? Roughly what deal size?_
- **Proof you can point to:**
  _Reference customers, case studies, certifications, uptime/SLA numbers — whatever a prospect would want to hear._

## 2. Who is your ideal customer?
- **Company size band:**
  _Employee count and/or revenue. Where's the sweet spot, and where's the floor/ceiling?_
- **Geography:**
  _Countries, states, cities. Any you prioritise because of proximity, licensing or language?_
- **Industries / verticals (in priority order):**
  _Which sectors feel the pain you solve most acutely?_
- **Who to EXCLUDE:**
  _Too big, too small, government, competitors, existing customers, companies that build this in-house._

## 3. What makes a company a good fit *right now*?
- **Firmographic fit signals:**
  _Observable traits that mean "this is our kind of company" (e.g. runs its own infrastructure, holds regulated data, has a small team in area X)._
- **Timing triggers (the "why now"):**
  _Dated events that make a company more likely to buy soon — new leader in a role, a hiring spree, a funding round, M&A, a renewal cliff, a public incident, rapid growth._
- **Disqualifiers:**
  _Anything that, if true, means don't bother._

## 4. Who do you want to reach inside each company?
- **Primary persona (feels the pain, takes the first call):**
  _Job titles._
- **Economic buyer / budget holder:**
  _Job titles._
- **Any other persona worth contacting:**
  _Job titles — and who NOT to contact (so you don't pay to enrich the wrong people)._

## 5. Budget and guardrails
- **Spend per run:**
  _How much are you willing to pay in data costs for one batch of leads? (The example runs cost US$6–9 for ~40 accounts.)_
- **Per-contact ceiling:**
  _Cap on a single lookup so one expensive call can't blow the budget._
- **Compliance notes:**
  _Any rules for your market — in Australia that's the Privacy Act, Spam Act (inferred consent for cold email) and the Do Not Call Register. Swap in your jurisdiction's equivalents._

---

<details>
<summary><b>📋 Completed example — managed hosting provider, AU launch</b></summary>

<br/>

Researched October 2026 from public sources. Treat this as a worked example of the
answers above, not as your configuration — replace it with your own.

### 1. What they sell
- **One sentence:** Fully-managed hosting and private cloud, hosted in Australia, with 24/7 direct-to-engineer support.
- **Why a buyer switches:**
  - 🇦🇺 Australian-hosted private cloud / VPC / dedicated servers / managed AWS & Azure, so data stays under Australian jurisdiction.
  - 🧑‍🔧 Direct-to-engineer 24/7 support, response under 20 minutes — matters most to firms with a 2–5 person IT team and no after-hours cover.
  - 📊 Fixed monthly billing — an alternative to unpredictable hyperscaler bills and VMware/Broadcom licence shocks.
  - 🛠️ Bespoke design by engineers, 100% network uptime SLA, 99.99% cloud uptime.
- **Commercial model:** Managed-service subscription, typically multi-year infrastructure contracts.
- **Proof:** Secure healthcare platforms, high-performance eCommerce hosting built for traffic spikes; serves eCommerce, financial services, healthcare, AI/ML, education.

### 2. Ideal customer
- **Size:** ~100–1,000 employees (A$20m–A$500m revenue); 50–100 acceptable with strong signals.
- **Geography:** Australian HQ; NSW and VIC first (closest to the Sydney/Melbourne data centres), then QLD, WA, SA.
- **Verticals:** `1` Healthcare & allied health · `2` Non-bank financial services · `3` Professional services · `4` eCommerce · `5` Education · `6` Logistics & manufacturing · `7` AU-hosted SaaS.
- **Exclude:** Tier-1 orgs (big banks, major insurers, mega super funds, ASX 200 and their subsidiaries), government, hosting competitors, and any firm with more than ~40 in-house IT staff.

### 3. Good fit right now
- **Firmographic signals:** Runs its own infrastructure (on-prem, VMware, colocation, legacy hosting) or a cloud estate it struggles to manage; holds sensitive/regulated data; small IT team.
- **Timing triggers:** New IT leader in the last 12 months, infrastructure job ads (VMware, systems/infra engineer), M&A, a cyber incident, rapid growth, VMware/Broadcom licence pain, hardware refresh due, office/data-centre move, cloud-cost blowout.
- **Disqualifiers:** >~2,000 staff, fully cloud-native startups with a strong in-house DevOps team (unless they show cloud-cost pain).

### 4. Personas
- **P1 · IT lead (first call):** IT Manager, Head of IT, Infrastructure Manager, IT Ops Manager.
- **P2 · IT executive (budget/strategy):** CIO, IT Director, CTO, Chief Digital Officer.
- **P3 · Finance/ops (signs the contract):** CFO, COO (CEO at smaller firms with no IT lead).
- **Do not contact / don't pay to enrich:** sales, account managers, project managers, consultants, lawyers, recruiters, interns.

### 5. Budget
- **Per run:** US$10. **Per contact:** US$0.50 ceiling. Example runs landed at US$5.96–9.02 for 38–40 accounts.
- **Compliance:** Privacy Act 1988 (prospect data is personal information), Spam Act 2003 (cold email needs inferred consent — record where each address came from), Do Not Call Register (wash mobiles before calling at volume).

### Talk tracks by pain (example)
| Pain the prospect has | Angle |
|---|---|
| VMware/Broadcom licence renewal shock | Move VMs to managed private cloud/VPC; the provider carries the platform licensing and ops |
| Ageing on-prem servers, hardware refresh due | Avoid capex; migrate to managed private cloud in Australian data centres |
| Data must stay in Australia | Australian-hosted, Australian jurisdiction |
| Small IT team, no after-hours cover | Direct-to-engineer 24/7 support as an extension of their team |
| AWS/Azure bill blowing out | Managed AWS/Azure, or repatriate steady workloads to fixed-price private cloud |
| Post-breach / Essential Eight / board cyber pressure | Managed security services on hardened infrastructure |

</details>
