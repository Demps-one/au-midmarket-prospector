#!/usr/bin/env python3
"""Merge new rows into a master prospecting CSV, deduplicating.

Usage: merge_list.py accounts|contacts|partners <new_rows.csv>

- accounts/partners: dedupe by normalised domain. If a company already exists,
  the higher-scored row's research wins, but the BDM's `status` is always kept.
- contacts: dedupe by email (or by domain + full_name when there is no email).
Prints a summary of added/updated/skipped rows.
"""
import csv, os, re, sys, datetime

def data_dir():
    """PROSPECT_DATA_DIR, else data/ at the repo root (repo/.claude/skills/<skill>/scripts), else ~/prospecting/au."""
    if os.environ.get("PROSPECT_DATA_DIR"):
        return os.path.expanduser(os.environ["PROSPECT_DATA_DIR"])
    repo_data = os.path.join(os.path.dirname(os.path.realpath(__file__)), *[".."] * 4, "data")
    if os.path.isdir(repo_data):
        return os.path.normpath(repo_data)
    return os.path.expanduser("~/prospecting/au")

DIR = data_dir()
COLUMNS = {
    "accounts": "company,domain,abn,hq_state,industry,employees,revenue_aud_est,score,tier,why_fit,infra_signals,triggers,trigger_dates,found_via,source_urls,date_added,status",
    "contacts": "domain,company,full_name,title,persona,in_role_since,location,linkedin_url,email,email_verdict,email_unverified,phone,phone_verdict,contact_source,date_added",
    "partners": "company,domain,hq_state,type,notes,source_urls,date_added",
}


def norm_domain(d):
    d = (d or "").strip().lower()
    d = re.sub(r"^https?://", "", d)
    d = re.sub(r"^www\.", "", d)
    return d.split("/")[0]


def key(kind, row):
    if kind == "contacts":
        email = (row.get("email") or row.get("email_unverified") or "").strip().lower()
        return email or f"{norm_domain(row.get('domain'))}|{(row.get('full_name') or '').strip().lower()}"
    return norm_domain(row.get("domain")) or (row.get("company") or "").strip().lower()


def score(row):
    try:
        return float(row.get("score") or 0)
    except ValueError:
        return 0.0


def main():
    if len(sys.argv) != 3 or sys.argv[1] not in COLUMNS:
        sys.exit(__doc__)
    kind, new_path = sys.argv[1], sys.argv[2]
    cols = COLUMNS[kind].split(",")
    master = os.path.join(DIR, f"{kind}.csv")
    os.makedirs(DIR, exist_ok=True)

    rows, order = {}, []
    if os.path.exists(master):
        with open(master, newline="") as f:
            for r in csv.DictReader(f):
                k = key(kind, r)
                if k not in rows:
                    order.append(k)
                rows[k] = r

    added = updated = skipped = 0
    today = datetime.date.today().isoformat()
    with open(new_path, newline="") as f:
        for r in csv.DictReader(f):
            if "domain" in r:
                r["domain"] = norm_domain(r["domain"])
            r.setdefault("date_added", today)
            r["date_added"] = r["date_added"] or today
            k = key(kind, r)
            if not k:
                skipped += 1
                continue
            if k not in rows:
                if kind == "accounts":
                    r["status"] = r.get("status") or "new"
                rows[k] = r
                order.append(k)
                added += 1
                continue
            old = rows[k]
            if kind == "accounts" and score(r) <= score(old):
                skipped += 1
                continue
            merged = {c: (r.get(c) or old.get(c) or "") for c in cols}
            merged["date_added"] = old.get("date_added") or today
            if kind == "accounts":
                merged["status"] = old.get("status") or "new"
            rows[k] = merged
            updated += 1

    with open(master, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore", lineterminator="\n")
        w.writeheader()
        for k in order:
            w.writerow({c: rows[k].get(c, "") for c in cols})
    print(f"{kind}: +{added} added, {updated} updated, {skipped} skipped -> {master} ({len(order)} total)")


if __name__ == "__main__":
    main()
