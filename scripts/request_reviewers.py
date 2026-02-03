import os, requests, sys
owner='stefmaf09-droid'
repo='E-commerce'
pull=1
url=f'https://api.github.com/repos/{owner}/{repo}/pulls/{pull}/requested_reviewers'
headers={'Authorization':f"token {os.environ.get('GITHUB_TOKEN')}",'Accept':'application/vnd.github+json'}
try:
    resp=requests.post(url, headers=headers, json={'reviewers':['stefmaf09-droid']}, timeout=15)
    print('STATUS', resp.status_code)
    print(resp.json())
except Exception as e:
    print('ERROR while requesting reviewers:', e)
    sys.exit(1)
