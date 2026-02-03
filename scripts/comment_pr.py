import os, requests, sys
owner='stefmaf09-droid'
repo='E-commerce'
issue=1
url=f'https://api.github.com/repos/{owner}/{repo}/issues/{issue}/comments'
headers={'Authorization':f"token {os.environ.get('GITHUB_TOKEN')}",'Accept':'application/vnd.github+json'}
try:
    resp=requests.post(url, headers=headers, json={'body':'Docs: added `Security & Automations` section to README and pushed to this branch.'}, timeout=15)
    print('STATUS', resp.status_code)
    print(resp.json())
except Exception as e:
    print('ERROR while commenting PR:', e)
    sys.exit(1)
