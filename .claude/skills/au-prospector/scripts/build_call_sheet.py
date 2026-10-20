#!/usr/bin/env python3
"""Build a BDM call sheet (one row per contact, with account context) from the master lists.

Usage:
  build_call_sheet.py OUT.csv [--industry TEXT] [--date YYYY-MM-DD] [--states NSW,VIC] [--dir DATA_DIR]

--industry matches a substring of accounts.industry (case-insensitive), e.g. "Allied health".
--date keeps only accounts added on that date.
Rows are grouped by state, then sorted by score (highest first), then persona.
"""
import argparse, csv, os, re

COLS = ["list", "tier", "score", "company", "employees", "segment", "full_name", "title", "persona",
        "mobile", "mobile_status", "email", "email_status", "linkedin_url", "why_fit", "notes"]


def data_dir():
    """PROSPECT_DATA_DIR, else data/ at the repo root (repo/.claude/skills/<skill>/scripts), else ~/prospecting/au."""
    if os.environ.get("PROSPECT_DATA_DIR"):
        return os.path.expanduser(os.environ["PROSPECT_DATA_DIR"])
    repo_data = os.path.join(os.path.dirname(os.path.realpath(__file__)), *[".."] * 4, "data")
    if os.path.isdir(repo_data):
        return os.path.normpath(repo_data)
    return os.path.expanduser("~/prospecting/au")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--industry")
    ap.add_argument("--date")
    ap.add_argument("--states")
    ap.add_argument("--dir", default=data_dir())
    a = ap.parse_args()
    d = os.path.expanduser(a.dir)
    accounts = list(csv.DictReader(open(os.path.join(d, "accounts.csv"), newline="")))
    contacts = list(csv.DictReader(open(os.path.join(d, "contacts.csv"), newline="")))
    states = set(a.states.split(",")) if a.states else None

    acc = {}
    for r in accounts:
        if a.industry and a.industry.lower() not in r["industry"].lower():
            continue
        if a.date and r["date_added"] != a.date:
            continue
        if states and r["hq_state"] not in states:
            continue
        acc[r["domain"]] = r

    rows = []
    for c in contacts:
        r = acc.get(c["domain"])
        if not r:
            continue
        src = c.get("contact_source", "")
        notes = src.split("| NOTE:", 1)[1].strip() if "| NOTE:" in src else ""
        segment = re.split(r"\s+[—-]\s+", r["industry"], maxsplit=1)[-1]
        rows.append(dict(
            list=r["hq_state"], tier=r["tier"], score=r["score"], company=r["company"],
            employees=r["employees"], segment=segment, full_name=c["full_name"], title=c["title"],
            persona=c["persona"], mobile=c["phone"], mobile_status=c["phone_verdict"],
            email=c["email"] or c["email_unverified"], email_status=c["email_verdict"],
            linkedin_url=c["linkedin_url"], why_fit=r["why_fit"], notes=notes))

    rows.sort(key=lambda x: (x["list"], -int(x["score"] or 0), x["company"], x["persona"]))
    with open(a.out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLS)
        w.writeheader()
        w.writerows(rows)
    print(f"{len(rows)} contacts across {len({r['company'] for r in rows})} accounts -> {a.out}")


if __name__ == "__main__":
    main()
