#!/usr/bin/env python3
"""Utility to post a pip-audit summary comment to a PR. Not used directly in CI steps but useful standalone."""
import os, json, requests, sys

if __name__ == '__main__':
    token = os.environ.get('GITHUB_TOKEN')
    repo = os.environ.get('GITHUB_REPOSITORY')
    pr = os.environ.get('PR_NUM')
    if not token or not repo or not pr:
        print('GITHUB_TOKEN, GITHUB_REPOSITORY and PR_NUM required')
        sys.exit(1)
    try:
        with open('pip-audit.json') as f:
            data = json.load(f)
    except Exception as e:
        print('Cannot open pip-audit.json', e)
        sys.exit(1)
    levels = {'low':0,'medium':1,'high':2,'critical':3}
    entries = []
    for item in data:
        for v in item.get('vulns', []):
            sev = v.get('severity','').lower()
            if levels.get(sev, -1) >= 1:
                entries.append((sev, item.get('name'), v.get('id')))
    if not entries:
        print('No vulns >= medium')
        sys.exit(0)
    body = '### ⚠️ pip-audit report (vulnerabilities >= medium)\n\n'
    for sev,name,vid in entries:
        body += f'- **{name}** — severity **{sev}** — {vid}\n'
    body += '\n_This comment was posted automatically by the `pip-audit` workflow._'
    url = f'https://api.github.com/repos/{repo}/issues/{pr}/comments'
    r = requests.post(url, headers={'Authorization':f'token {token}','Accept':'application/vnd.github+json'}, json={'body': body}, timeout=15)
    print('status', r.status_code)
    print(r.text)
