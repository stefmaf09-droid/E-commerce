import os
import requests
import json

token = os.environ.get('GITHUB_TOKEN')
if not token:
    print('ERROR: GITHUB_TOKEN not found in environment')
    raise SystemExit(1)

owner = 'stefmaf09-droid'
repo = 'E-commerce'
url = f'https://api.github.com/repos/{owner}/{repo}/pulls'
headers = {
    'Authorization': f'token {token}',
    'Accept': 'application/vnd.github+json'
}
payload = {
    'title': 'chore: add PyPDF2 to requirements, CI install, docs and CI smoke test',
    'head': 'feat/add-pypdf2-ci-smoke',
    'base': 'main',
    'body': 'Ajout de PyPDF2 pour les vérifications PDF en tests. Installation explicite dans CI et test smoke CI ajouté (tests/test_py_pdf2_ci.py).',
    'draft': False
}

resp = requests.post(url, headers=headers, json=payload)
print('STATUS:', resp.status_code)
try:
    data = resp.json()
    print(json.dumps(data, indent=2))
except Exception:
    print(resp.text)
    raise SystemExit(1)

if resp.status_code in (200, 201):
    print('\nPR URL:', data.get('html_url'))
else:
    raise SystemExit(1)
