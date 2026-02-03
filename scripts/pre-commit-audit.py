#!/usr/bin/env python3
"""Simple cross-platform pre-commit style script to fail if pip-audit finds >= high"""
import json
import shutil
import subprocess
import sys

def run_pip_audit(json_out='pip-audit.json'):
    # Ensure pip-audit is installed
    if shutil.which('pip-audit') is None:
        print('pip-audit not found; installing (user may be prompted)...')
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pip-audit'])

    # Run pip-audit and write JSON
    cmd = ['pip-audit', '--format', 'json', '--output', json_out]
    print('Running:', ' '.join(cmd))
    subprocess.check_call(cmd)

    # Parse and enforce
    with open(json_out, 'r', encoding='utf8') as f:
        data = json.load(f)

    severity_rank = {'low':0, 'medium':1, 'high':2, 'critical':3}
    found = False
    for item in data:
        for vuln in item.get('vulns', []):
            sev = vuln.get('severity','').lower()
            if severity_rank.get(sev, -1) >= 2:
                print('VULN:', item.get('name'), 'severity=', sev, 'id=', vuln.get('id'))
                found = True
    if found:
        print('\npip-audit found vulnerabilities severity >= high. Commit aborted.')
        return 1
    print('No vulnerabilities >= high found.')
    return 0

if __name__ == '__main__':
    sys.exit(run_pip_audit())
