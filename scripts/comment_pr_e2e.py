import os, requests, sys
owner='stefmaf09-droid'
repo='E-commerce'
issue=1
url=f'https://api.github.com/repos/{owner}/{repo}/issues/{issue}/comments'
headers={'Authorization':f"token {os.environ.get('GITHUB_TOKEN')}",'Accept':'application/vnd.github+json'}
try:
    resp=requests.post(url, headers=headers, json={'body':'Added E2E Playwright onboarding smoke test, a Makefile target `make e2e` and a CI job `e2e` that runs the smoke test and uploads `streamlit_e2e.log` as artifact.'}, timeout=15)
    print('STATUS', resp.status_code)
    print(resp.json())
except Exception as e:
    print('ERROR while commenting PR:', e)
    sys.exit(1)
