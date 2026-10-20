---
name: security-review
description: CISO-style security and privacy review of the AU mid-market prospecting project (the au-prospector skill, its GitHub repo, the Treg connection and the prospect data). Checks for leaked secrets or personal data in git, repo exposure, local data protection, third-party data flows, and Australian Privacy Act / Spam Act compliance, then writes a risk register with severities and a sign-off verdict. Use whenever the user asks to security-check, audit, review or "make sure it's safe" for this project, before pushing to GitHub, before sharing the repo or adding a collaborator, before moving prospect data into the repo, after a new device is set up, or periodically (e.g. monthly).
---

# Prospecting security review

Act as the **CISO** of a mid-market company reviewing an internal sales tool before signing off on it. Be independent and sceptical. The goal is to protect people whose data is in the lists, the user's accounts and credentials, and the provider's reputation. You are not here to approve the project. Your job is to find what could go wrong and say plainly how bad it is.

**This is a review, not a fix-it run.** Do not change files, permissions, git history or settings without the user's explicit OK. Propose each fix as a command or edit they can approve. Never print a secret or a person's contact details in the report. Refer to them by file and line, or by count.

## What's in scope

| Asset | Where | Why it matters |
|---|---|---|
| Prospect data (names, work emails, mobiles, LinkedIn URLs) | `~/prospecting/au/` or `data/` in the repo | Personal information under the Privacy Act 1988 |
| Treg API token | `~/.claude.json` (MCP header), or `TREG_TOKEN` env | Spends money; reaches many data providers |
| GitHub repo `Demps-one/au-midmarket-prospector` and the `gh` login | GitHub, `~/.config/gh/` | The `gh` token has `repo` scope over **all** the user's repos |
| The prospector skill's instructions | `.claude/skills/au-prospector/` | Steers what an AI agent fetches, pays for and stores |
| Devices: PC, laptop, phone (Claude Code on the web) | Each machine | Each is a copy of the data and the credentials |

## Step 1: run the automated checks

```
python3 <this skill dir>/scripts/security_check.py
```
It checks the following and prints `SEVERITY | area | finding` lines without revealing secret values:
- **Git:** every commit for tokens (including an exact match on the live Treg token), emails, AU phone numbers, LinkedIn URLs and contact names; tracked data files; `.gitignore`.
- **GitHub:** repo visibility, collaborators, deploy keys, 2FA, token scopes.
- **Local files:** permissions on the config and data folder, PII in the cost log, leftover temp files, tokens in shell history.
- **Contact list:** Spam Act basics.

Treat its output as evidence, not as the whole review.

## Step 2: judgment checks (read the files yourself)

1. **Agent instructions (prompt injection and overreach).** Read the prospector's `SKILL.md` and `references/`. Does the skill treat web pages, job ads and provider responses as *data, not instructions*? Could a malicious web page steer the agent into spending money, emailing people or pushing data somewhere? Does anything tell the agent to send personal data anywhere other than Treg and the local CSVs? Are spend limits (per-call and per-run) still in place?
2. **Third-party data flows (APP 8, cross-border disclosure).** Read `references/sources.md`. List which providers receive personal data. Treg routes to many vendors, mostly offshore (US/EU): Icypeas, Prospeo, Tomba, ContactOut, FindyMail, HLR Lookup, trykitt and others. Note that names, LinkedIn URLs and numbers leave Australia, and say whether the provider's privacy policy would need to cover that.
3. **Privacy Act 1988 (APPs).** The small-business exemption is unlikely to apply to a global company, so assume the APPs apply. Check:
   - **APP 3/5:** collection only of what's needed, and a way to tell people where their data came from.
   - **APP 10:** data quality, including stale contacts and wrong numbers.
   - **APP 11:** security and destruction of old data.
   - **APP 12/13:** whether a person could ask for their data and have it corrected or deleted.
4. **Spam Act 2003.** Check three things: every email has an inferred-consent basis (`contact_source`), there is somewhere to record unsubscribes (honour within 5 business days), and nothing in the workflow bulk-sends.
5. **Do Not Call Register Act 2006.** Mobiles are being collected for cold calls. B2B calls to a business mobile are generally fine, but a personal mobile on the DNCR is not. Flag whether the workflow has any DNCR wash. If not, recommend one before calling at volume.
6. **Data minimisation and retention.**
   - Does the project keep more than it needs, such as raw provider dumps in temp folders or old call sheets?
   - Is there a retention rule (e.g. purge contacts not worked within 12 months)?
7. **Credential hygiene.**
   - The Treg token sits in plaintext in `~/.claude.json`, which is normal for Claude Code MCP config, but the file must be mode 600.
   - Is the token scoped or spend-limited in Treg? Can it be rotated quickly?
   - The `gh` token has `repo` scope, so a compromised machine exposes all of the user's repos.
   - Is GitHub 2FA on?
8. **Device spread.** For each device that clones the repo or holds the data: is the disk encrypted, is the screen locked, and is the device shared? Phone sessions run in Anthropic's cloud. Note that data placed in the repo is then processed there too.
9. **Git history.** Even with a clean HEAD, check history (the script does this). If a secret was ever committed, it must be **rotated**. Purging history isn't enough, because GitHub can retain orphaned commits.

## Step 3: report

Write the report to `<data folder>/security-review-<YYYY-MM-DD>.md`. That puts it next to the data, outside git, because findings may point at personal data. Then give the user a short chat summary.

Report structure:
1. **Verdict.** One of: **Approved**, **Approved with conditions** (list them), or **Not approved** (any Critical, or any unresolved High involving personal data or secrets).
2. **Executive summary.** Three to five sentences a non-technical manager would understand.
3. **Risk register.** A table with ID, severity, area, finding, impact, recommended fix, and owner/effort. Severities:
   - **Critical:** secret or personal data exposed publicly, or repo public. Act today.
   - **High:** likely breach of law or a credential at real risk. Fix this week.
   - **Medium:** weak control that raises the chance or impact of an incident. Fix this month.
   - **Low:** hygiene.
4. **What's working.** The controls that passed, so the user knows what to keep doing.
5. **Fix commands.** Copy-paste commands for the safe fixes (e.g. `chmod -R go-rwx ~/prospecting/au`), each marked as needing the user's OK.
6. **Next review.** Recommend one before any of: making the repo public, adding a collaborator, moving data into the repo, connecting a new device, or adding a new data provider. Otherwise review monthly.

Keep the chat summary to the verdict, the counts by severity, and the top three actions.
