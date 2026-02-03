#!/usr/bin/env python3
"""Create GitHub issues for backlog high-priority items."""
import os, requests, sys

GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
if not GITHUB_TOKEN:
    print('GITHUB_TOKEN required in env')
    sys.exit(1)

owner = 'stefmaf09-droid'
repo = 'E-commerce'
base_url = f'https://api.github.com/repos/{owner}/{repo}/issues'
headers = {'Authorization': f'token {GITHUB_TOKEN}', 'Accept':'application/vnd.github+json'}

issues = [
    {
        'title': 'E2E: Playwright tests for onboarding (signup -> redirect -> first-login)',
        'body': 'Add Playwright tests that simulate a new user signup, follow the magic link or auto-login, and verify redirection to the client dashboard with welcome message.\n\nCriteria:\n- test runs in CI on PRs\n- deterministic (mock external networks where needed)\n- include at least one smoke test for onboarding',
        'labels': ['e2e','ci','high-priority','backlog']
    },
    {
        'title': 'CI: Add Playwright E2E job to GitHub Actions (onboarding smoke)',
        'body': 'Create a GitHub Actions job that runs Playwright onboarding smoke tests in headless mode. Use a matrix to optionally run slow tests on demand and upload artifacts (screenshots & traces).',
        'labels': ['ci','e2e','backlog']
    },
    {
        'title': 'Reliability: Add retries and idempotence to Shopify connector',
        'body': 'Wrap Shopify API calls with retry (exponential backoff + jitter) and ensure idempotency for write operations using an idempotency key. Add unit and integration tests.',
        'labels': ['integrations','reliability','backlog']
    },
    {
        'title': 'Observability: Add structured audit logging for critical actions',
        'body': 'Implement `src/logging/audit.py` and emit structured JSON logs for events: user_created, user_login, stripe_activation, ticket_fallback_created. Add docs and examples.',
        'labels': ['observability','compliance','backlog']
    }
]

created = []
for it in issues:
    try:
        r = requests.post(base_url, headers=headers, json=it, timeout=15)
        print('STATUS', r.status_code)
        if r.status_code in (200,201):
            data = r.json()
            created.append((it['title'], data['html_url']))
        else:
            print('ERROR creating issue:', r.status_code, r.text)
    except Exception as e:
        print('EXC', e)

print('\nCreated issues:')
for t,u in created:
    print('-', t, '->', u)
