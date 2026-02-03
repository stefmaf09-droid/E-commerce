import os, requests
owner='stefmaf09-droid'
repo='E-commerce'
url=f'https://api.github.com/repos/{owner}/{repo}/branches'
headers={'Authorization':f"token {os.environ.get('GITHUB_TOKEN')}",'Accept':'application/vnd.github+json'}
resp=requests.get(url, headers=headers, params={'per_page':100}, timeout=10)
print('STATUS', resp.status_code)
if resp.status_code==200:
    branches=[b['name'] for b in resp.json()]
    print('branches_count:', len(branches))
    for b in branches[:50]:
        print(b)
else:
    print(resp.text)
    raise SystemExit(1)
