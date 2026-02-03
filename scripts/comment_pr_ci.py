import os, requests, sys
owner='stefmaf09-droid'
repo='E-commerce'
issue=1
url=f'https://api.github.com/repos/{owner}/{repo}/issues/{issue}/comments'
headers={'Authorization':f"token {os.environ.get('GITHUB_TOKEN')}",'Accept':'application/vnd.github+json'}
try:
    resp=requests.post(url, headers=headers, json={'body':'CI update: added pip-audit JSON report artifact and a fail-on-high check; README updated with local pip-audit usage instructions. The pipeline will now upload `pip-audit.json` and fail if any vulnerability with severity >= high is found.'}, timeout=15)
    print('STATUS', resp.status_code)
    print(resp.json())
except Exception as e:
    print('ERROR while commenting PR:', e)
    sys.exit(1)
