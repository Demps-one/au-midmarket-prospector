#!/usr/bin/env python3
"""Call a Treg endpoint with a cost ceiling, run budget and spend log.

Usage:
  treg_call.py <endpoint-id> [--query k=v ...] [--json '{"k":"v"}'] [--method GET|POST]
               [--max-cost 0.25] [--verify] [--budget 2.00]
  treg_call.py --spent            # total spend logged today and all-time

Prints the JSON response body to stdout; cost and call id go to stderr.
"""
import argparse, datetime, json, os, sys, urllib.error, urllib.parse, urllib.request, uuid

BASE = "https://treg.to/call/"
def data_dir():
    """PROSPECT_DATA_DIR, else data/ at the repo root (repo/.claude/skills/<skill>/scripts), else ~/prospecting/au."""
    if os.environ.get("PROSPECT_DATA_DIR"):
        return os.path.expanduser(os.environ["PROSPECT_DATA_DIR"])
    repo_data = os.path.join(os.path.dirname(os.path.realpath(__file__)), *[".."] * 4, "data")
    if os.path.isdir(repo_data):
        return os.path.normpath(repo_data)
    return os.path.expanduser("~/prospecting/au")

LOG = os.path.join(data_dir(), "costs.log")


def spent(today_only=False):
    total = 0.0
    if not os.path.exists(LOG):
        return total
    today = datetime.date.today().isoformat()
    with open(LOG) as f:
        for line in f:
            parts = line.rstrip("\n").split("\t")
            if len(parts) >= 3 and (not today_only or parts[0].startswith(today)):
                total += float(parts[2])
    return total


def main():
    p = argparse.ArgumentParser()
    p.add_argument("endpoint", nargs="?")
    p.add_argument("--query", action="append", default=[], help="k=v query param (repeatable)")
    p.add_argument("--json", help="JSON request body (implies POST)")
    p.add_argument("--method")
    p.add_argument("--max-cost", type=float, default=0.25, help="USD ceiling for this call")
    p.add_argument("--budget", type=float, default=float(os.environ.get("PROSPECT_TREG_BUDGET", 2.0)),
                   help="USD ceiling for today's total spend")
    p.add_argument("--verify", action="store_true", help="verify found email/phone inline")
    p.add_argument("--spent", action="store_true")
    a = p.parse_args()

    if a.spent:
        print(f"today: ${spent(True):.4f}  all-time: ${spent():.4f}")
        return
    if not a.endpoint:
        p.error("endpoint required")
    token = os.environ.get("TREG_TOKEN")
    if not token:
        sys.exit("TREG_TOKEN not set; sign up at https://treg.to and export TREG_TOKEN")

    today = spent(True)
    if today + a.max_cost > a.budget:
        sys.exit(f"budget stop: spent ${today:.4f} today, budget ${a.budget:.2f}")

    url = BASE + a.endpoint
    if a.query:
        url += "?" + urllib.parse.urlencode([q.split("=", 1) for q in a.query])
    body = a.json.encode() if a.json else None
    method = a.method or ("POST" if body else "GET")
    headers = {
        "X-Treg-Token": token,
        "X-Treg-Route-Max-Cost": str(a.max_cost),
        "Idempotency-Key": str(uuid.uuid4()),
        "Accept": "application/json",
    }
    if body:
        headers["Content-Type"] = "application/json"
    if a.verify:
        headers["X-Treg-Route-Verify"] = "true"

    req = urllib.request.Request(url, data=body, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            status, hdrs, data = r.status, r.headers, r.read()
    except urllib.error.HTTPError as e:
        status, hdrs, data = e.code, e.headers, e.read()

    cost = int(hdrs.get("X-Treg-Cost-Micro") or 0) / 1e6
    call_id = hdrs.get("X-Treg-Call-Id", "")
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    with open(LOG, "a") as f:
        f.write(f"{datetime.datetime.now().isoformat(timespec='seconds')}\t{a.endpoint}\t{cost:.6f}\t{status}\t{call_id}\n")
    print(f"[treg] {a.endpoint} status={status} cost=${cost:.4f} call_id={call_id}", file=sys.stderr)
    sys.stdout.write(data.decode(errors="replace"))
    if status >= 400:
        sys.exit(1)


if __name__ == "__main__":
    main()
