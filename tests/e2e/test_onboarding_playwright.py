import os
import subprocess
import sys
import time
import requests
import pytest

try:
    from playwright.sync_api import sync_playwright
except Exception:
    pytest.skip("Playwright not installed; skipping e2e tests", allow_module_level=True)

PORT = int(os.environ.get('E2E_PORT', 8510))
URL = f'http://localhost:{PORT}'
STREAMLIT_CMD = [sys.executable, '-m', 'streamlit', 'run', 'dashboard.py', '--server.port', str(PORT)]


def wait_for_server(url, timeout=30):
    start = time.time()
    while time.time() - start < timeout:
        try:
            r = requests.get(url, timeout=2)
            if r.status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(0.5)
    return False


def start_streamlit():
    env = os.environ.copy()
    # Make sure Streamlit does not try to open an external browser
    env['BROWSER'] = 'none'
    logfile = open('streamlit_e2e.log', 'wb')
    proc = subprocess.Popen(STREAMLIT_CMD, env=env, stdout=logfile, stderr=logfile)
    return proc, logfile


def stop_process(proc, logfile):
    try:
        proc.terminate()
        proc.wait(timeout=5)
    except Exception:
        proc.kill()
    try:
        logfile.close()
    except Exception:
        pass


def test_onboarding_smoke():
    proc, log = start_streamlit()
    try:
        assert wait_for_server(URL, timeout=60), 'Streamlit server did not start in time; check streamlit_e2e.log'

        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(URL, timeout=30000)
            content = page.content()
            # Look for auth entry points we added (Se connecter / S'inscrire)
            assert ('Se connecter' in content) or ('S\'inscrire' in content) or ('Se connecter / S\'inscrire' in content), \
                'Expected auth links text not found on landing page'
            browser.close()
    finally:
        stop_process(proc, log)
