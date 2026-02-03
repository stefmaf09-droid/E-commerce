import os, requests, sys
owner='stefmaf09-droid'
repo='E-commerce'
issue=1
url=f'https://api.github.com/repos/{owner}/{repo}/issues/{issue}/comments'
headers={'Authorization':f"token {os.environ.get('GITHUB_TOKEN')}",'Accept':'application/vnd.github+json'}
try:
    resp=requests.post(url, headers=headers, json={'body':'Added dedicated `pip-audit` workflow (weekly & on push), Makefile `audit` target, and `scripts/pre-commit-audit.py` to enable local pre-commit checks. Also added a pipeline badge linking to the `pip-audit` workflow.'}, timeout=15)
    print('STATUS', resp.status_code)
    print(resp.json())
except Exception as e:
    print('ERROR while commenting PR:', e)
    sys.exit(1)
