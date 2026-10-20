#!/usr/bin/env python3
"""Automated security checks for the au-midmarket-prospector project.

Prints one line per check: SEVERITY | area | finding. Never prints secret values or personal data:
matches are reported as file:line plus a masked hint only.

Usage: security_check.py [--repo PATH] [--data PATH] [--staged | --git-only]

  --staged    pre-commit mode: scan only the files staged for commit (fast)
  --git-only  CI mode: git history checks only (no GitHub API, local files or data)
Exit code is 1 if any CRITICAL or HIGH finding, so hooks and CI can block on it.
"""
import argparse, csv, glob, json, os, re, stat, subprocess

SEV_ORDER = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "PASS", "INFO", "MANUAL"]
results = []


def add(sev, area, msg):
    results.append((sev, area, msg))


def run(cmd, cwd=None):
    try:
        return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=60).stdout
    except Exception:
        return ""


def mask(s):
    return s[:3] + "…" + str(len(s)) if len(s) > 6 else "…"


def data_dir():
    if os.environ.get("PROSPECT_DATA_DIR"):
        return os.path.expanduser(os.environ["PROSPECT_DATA_DIR"])
    return os.path.expanduser("~/prospecting/au")


def repo_root():
    here = os.path.dirname(os.path.realpath(__file__))
    return run(["git", "rev-parse", "--show-toplevel"], cwd=here).strip()


SECRET_PATTERNS = {
    "bearer token": r"Bearer\s+[A-Za-z0-9._\-]{16,}",
    "GitHub token": r"\b(ghp|gho|ghu|ghs|github_pat)_[A-Za-z0-9_]{20,}",
    "AWS key": r"\bAKIA[0-9A-Z]{16}\b",
    "API key assignment": r"(?i)(api[_-]?key|token|secret|password)\s*[:=]\s*['\"][A-Za-z0-9._\-]{16,}['\"]",
    "private key": r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
}
PII_PATTERNS = {
    "email address": r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
    "AU mobile": r"(\+?61|\b0)[ -]?4[0-9]{2}[ -]?[0-9]{3}[ -]?[0-9]{3}\b",
    "AU landline": r"(\+?61[ -]?[2378]|\b0[2378])[ -]?[0-9]{4}[ -]?[0-9]{4}\b",
    "LinkedIn profile": r"linkedin\.com/in/[A-Za-z0-9\-_%]+",
}
EMAIL_ALLOW = re.compile(r"noreply@anthropic\.com|@example\.(com|org)|user@|name@|first\.last@", re.I)


def treg_token():
    """Return the Treg token from Claude Code config or env, for exact-match leak checks only."""
    toks = []
    if os.environ.get("TREG_TOKEN"):
        toks.append(os.environ["TREG_TOKEN"])
    try:
        d = json.load(open(os.path.expanduser("~/.claude.json")))

        def walk(o):
            if isinstance(o, dict):
                for k, v in o.items():
                    if k == "mcpServers" and isinstance(v, dict) and "treg" in v:
                        h = v["treg"].get("headers", {}).get("Authorization", "")
                        if h:
                            toks.append(h.split()[-1])
                    walk(v)
        walk(d)
    except Exception:
        pass
    return [t for t in toks if len(t) >= 12]


def check_git(repo, contacts):
    if not repo:
        add("INFO", "git", "Skill is not inside a git repo; git checks skipped")
        return
    revs = run(["git", "rev-list", "--all"], cwd=repo).split()
    add("INFO", "git", f"Scanning {len(revs)} commit(s) in {repo}")
    tracked = run(["git", "ls-files"], cwd=repo).split("\n")

    bad = [f for f in tracked if re.search(r"\.(csv|tsv|xlsx|json|env|log)$|(^|/)data/", f) and f]
    add("HIGH" if bad else "PASS", "git", f"Data-type files tracked: {', '.join(bad)}" if bad
        else "No CSV/TSV/JSON/log/env or data/ files tracked")

    def grep_all(pattern):
        if not revs:
            return []
        out = run(["git", "grep", "-nIE", pattern] + revs, cwd=repo)
        return [l for l in out.splitlines() if l]

    for name, pat in SECRET_PATTERNS.items():
        hits = grep_all(pat)
        if hits:
            locs = sorted({":".join(h.split(":")[1:3]) for h in hits})[:5]
            add("CRITICAL", "secrets", f"{name} pattern in git history at {locs}. Rotate the credential, then purge history")
    for t in treg_token():
        if grep_all(re.escape(t)):
            add("CRITICAL", "secrets", f"The live Treg token ({mask(t)}) is in git history. Rotate it in Treg now")
    if not any(r[1] == "secrets" for r in results):
        add("PASS", "secrets", "No tokens, keys or the live Treg token found in any commit")

    pii_found = False
    for name, pat in PII_PATTERNS.items():
        hits = grep_all(pat)
        if name == "email address":
            hits = [h for h in hits if not EMAIL_ALLOW.search(h)]
        if hits:
            pii_found = True
            locs = sorted({":".join(h.split(":")[1:3]) for h in hits})[:5]
            add("HIGH", "pii", f"{len(hits)} {name} match(es) in git history, e.g. {locs}")
    names = sorted({c["full_name"] for c in contacts if len(c.get("full_name", "")) > 5})
    if names and revs:
        head_files = {f: run(["git", "show", f"HEAD:{f}"], cwd=repo) for f in tracked if f}
        hits = [(n, f) for n in names for f, t in head_files.items() if n in t]
        if hits:
            pii_found = True
            add("HIGH", "pii", f"{len(hits)} contact full name(s) appear in tracked files: {sorted({f for _, f in hits})}")
    if not pii_found:
        add("PASS", "pii", f"No emails, phones, LinkedIn URLs or any of {len(names)} contact names in the repo")

    ignored = subprocess.run(["git", "check-ignore", "-q", "data/contacts.csv"], cwd=repo).returncode == 0
    add("PASS" if ignored else "HIGH", "git", "data/ is git-ignored" if ignored else "data/ is NOT git-ignored")


def check_staged(repo, contacts):
    """Pre-commit: scan the staged version of every added/changed file."""
    files = [f for f in run(["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"], cwd=repo).split("\n") if f]
    names = sorted({c["full_name"] for c in contacts if len(c.get("full_name", "")) > 5})
    tokens = treg_token()
    for f in files:
        if re.search(r"\.(csv|tsv|xlsx|json|env|log)$|(^|/)data/", f):
            add("HIGH", "commit", f"{f}: data-type file staged. Unstage it with: git restore --staged {f}")
            continue
        text = run(["git", "show", f":{f}"], cwd=repo)
        for i, line in enumerate(text.splitlines(), 1):
            for name, pat in SECRET_PATTERNS.items():
                if re.search(pat, line):
                    add("CRITICAL", "commit", f"{f}:{i}: looks like a {name}")
            if any(t in line for t in tokens):
                add("CRITICAL", "commit", f"{f}:{i}: contains the live Treg token")
            for name, pat in PII_PATTERNS.items():
                m = re.search(pat, line)
                if m and not (name == "email address" and EMAIL_ALLOW.search(line)):
                    add("HIGH", "commit", f"{f}:{i}: {name} ({mask(m.group(0))})")
            for n in names:
                if n in line:
                    add("HIGH", "commit", f"{f}:{i}: a contact's full name from contacts.csv")
    if not results:
        add("PASS", "commit", f"{len(files)} staged file(s) clean")


def check_github(repo):
    if not repo or not run(["which", "gh"]).strip():
        add("MANUAL", "github", "gh CLI not available; check repo visibility and 2FA on github.com")
        return
    info = run(["gh", "repo", "view", "--json", "nameWithOwner,visibility"], cwd=repo)
    try:
        info = json.loads(info)
        vis = info["visibility"]
        add("PASS" if vis == "PRIVATE" else "CRITICAL", "github", f"{info['nameWithOwner']} visibility is {vis}")
        collab = run(["gh", "api", f"repos/{info['nameWithOwner']}/collaborators", "--jq", ".[].login"], cwd=repo).split()
        add("INFO" if len(collab) <= 1 else "MEDIUM", "github", f"Collaborators: {', '.join(collab) or 'unknown'}")
        keys = run(["gh", "api", f"repos/{info['nameWithOwner']}/keys", "--jq", "length"], cwd=repo).strip()
        if keys and keys != "0":
            add("MEDIUM", "github", f"{keys} deploy key(s) on the repo. Confirm each is expected")
    except Exception:
        add("MANUAL", "github", "Could not read repo info via gh; check visibility on github.com")
    tfa = run(["gh", "api", "user", "--jq", ".two_factor_authentication"]).strip()
    if tfa == "true":
        add("PASS", "github", "GitHub account has 2FA enabled")
    elif tfa == "false":
        add("HIGH", "github", "GitHub account does NOT have 2FA. Enable it at github.com/settings/security")
    else:
        add("MANUAL", "github", "2FA status not visible with current token scopes. Confirm at github.com/settings/security")
    scopes = re.findall(r"Token scopes: (.*)", run(["gh", "auth", "status"]) + subprocess.run(
        ["gh", "auth", "status"], capture_output=True, text=True).stderr)
    if scopes:
        add("INFO", "github", f"gh token scopes: {scopes[0]}. 'repo' grants access to ALL your repos on this machine")


def mode(p):
    return stat.S_IMODE(os.stat(p).st_mode)


def check_local(ddir):
    cfg = os.path.expanduser("~/.claude.json")
    if os.path.exists(cfg):
        m = mode(cfg)
        add("PASS" if not m & 0o077 else "HIGH", "secrets",
            f"~/.claude.json (holds the Treg token in plaintext) mode {oct(m)}" + ("" if not m & 0o077 else ". Run chmod 600"))
    if not os.path.isdir(ddir):
        add("INFO", "data", f"No data folder at {ddir}")
        return
    m = mode(ddir)
    add("MEDIUM" if m & 0o007 else "PASS", "data",
        f"Data folder {ddir} mode {oct(m)}" + (". Other local users can read it; run chmod -R go-rwx" if m & 0o007 else ""))
    loose = [os.path.basename(f) for f in glob.glob(os.path.join(ddir, "*")) if mode(f) & 0o004]
    if loose:
        add("MEDIUM", "data", f"{len(loose)} data file(s) world-readable (e.g. {loose[:3]})")
    log = os.path.join(ddir, "costs.log")
    if os.path.exists(log):
        txt = open(log, errors="ignore").read()
        leak = any(re.search(p, txt) for p in PII_PATTERNS.values()) or any(t in txt for t in treg_token())
        add("HIGH" if leak else "PASS", "data", "costs.log contains PII or a token" if leak else "costs.log holds no PII or tokens")
    # leftover working files containing personal data outside the data folder
    tmp = [f for f in glob.glob(f"/tmp/claude-{os.getuid()}/**/*", recursive=True)
           if f.endswith((".csv", ".tsv", ".json")) and os.path.isfile(f)]
    pii_tmp = []
    for f in tmp:
        try:
            if re.search(PII_PATTERNS["email address"], open(f, errors="ignore").read(200000)):
                pii_tmp.append(f)
        except Exception:
            pass
    if pii_tmp:
        add("LOW", "data", f"{len(pii_tmp)} temp working file(s) with contact data under /tmp/claude-{os.getuid()} "
            "(cleared on reboot; delete sooner if the PC is shared)")
    hist = [h for h in ("~/.bash_history", "~/.zsh_history", "~/.local/share/fish/fish_history") if os.path.exists(os.path.expanduser(h))]
    for h in hist:
        txt = open(os.path.expanduser(h), errors="ignore").read()
        if re.search(r"Bearer\s+[A-Za-z0-9._\-]{16,}|TREG_TOKEN=\S{12,}", txt):
            add("MEDIUM", "secrets", f"A token appears in shell history {h}. Remove that line and consider rotating it")


def check_compliance(ddir, contacts):
    if not contacts:
        return
    no_src = sum(1 for c in contacts if c.get("email") or c.get("email_unverified")) - sum(
        1 for c in contacts if (c.get("email") or c.get("email_unverified")) and c.get("contact_source"))
    add("PASS" if no_src == 0 else "HIGH", "spam-act",
        f"{no_src} contact(s) with an email but no contact_source" if no_src else "Every email has a contact_source (Spam Act inferred-consent evidence)")
    cols = contacts[0].keys()
    if not any(k in cols for k in ("status", "do_not_contact", "unsubscribed", "opt_out")):
        add("MEDIUM", "spam-act", "contacts.csv has no opt-out / do-not-contact column. Spam Act s18 requires unsubscribes "
            "to be honoured within 5 business days, so the list needs somewhere to record them")
    dates = sorted(c.get("date_added", "") for c in contacts if c.get("date_added"))
    add("INFO", "privacy", f"{len(contacts)} contacts held; oldest added {dates[0] if dates else 'unknown'}. "
        "APP 11.2: destroy or de-identify data no longer needed")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo")
    ap.add_argument("--data")
    ap.add_argument("--staged", action="store_true")
    ap.add_argument("--git-only", action="store_true")
    a = ap.parse_args()
    repo = a.repo or repo_root()
    ddir = a.data or (os.path.join(repo, "data") if repo and os.path.isdir(os.path.join(repo, "data")) else data_dir())
    cpath = os.path.join(ddir, "contacts.csv")
    contacts = list(csv.DictReader(open(cpath, newline=""))) if os.path.exists(cpath) else []
    if a.staged:
        check_staged(repo, contacts)
    else:
        check_git(repo, contacts)
        if not a.git_only:
            check_github(repo)
            check_local(ddir)
            check_compliance(ddir, contacts)
    for sev, area, msg in sorted(results, key=lambda r: SEV_ORDER.index(r[0])):
        print(f"{sev:8} | {area:9} | {msg}")
    return 1 if any(r[0] in ("CRITICAL", "HIGH") for r in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
