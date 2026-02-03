import os, requests
owner='stefmaf09-droid'
repo='E-commerce'
url=f'https://api.github.com/repos/{owner}/{repo}'
headers={'Authorization':f"token {os.environ.get('GITHUB_TOKEN')}",'Accept':'application/vnd.github+json'}
resp=requests.get(url, headers=headers)
print('STATUS', resp.status_code)
if resp.status_code==200:
    data=resp.json()
    print('default_branch:', data.get('default_branch'))
else:
    print(resp.text)
    raise SystemExit(1)
