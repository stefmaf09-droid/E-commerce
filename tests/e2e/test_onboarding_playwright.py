import os
import subprocess
import sys
import time
import urllib.parse
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


def wait_for_text(page, text, timeout=20000):
    """Poll the DOM (via Playwright's text engine) until `text` appears.

    Streamlit reruns the page over its websocket connection rather than
    doing a full browser navigation, so this is the reliable way to wait
    for a rerun to land instead of a fixed sleep.
    """
    page.wait_for_selector(f"text={text}", timeout=timeout)


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


def test_registration_redirect_first_login():
    """Full E2E coverage for issue #2: inscription -> redirection -> premiere connexion.

    This goes beyond test_onboarding_smoke (which only checks the landing
    page renders auth links) by driving the real flow end to end:

    1. Land on the marketing page and reveal the auth tabs.
    2. Fill out and submit the real registration form (a brand new,
       unique throwaway account).
    3. Assert the registration redirects straight into the onboarding
       wizard (this is the "redirection" step from the issue).
    4. Log out.
    5. Log back in with the same credentials and assert the first login
       after registration succeeds (no error, lands back in onboarding
       since it was never completed).

    Uses a unique, timestamped email per run so the test is safe to
    re-run locally against a persistent SQLite/Postgres backend without
    colliding with a previous run's account.
    """
    proc, log = start_streamlit()
    try:
        assert wait_for_server(URL, timeout=60), 'Streamlit server did not start in time; check streamlit_e2e.log'

        test_email = f"e2e.pw.test.{int(time.time())}@example.com"
        test_password = "TestPass123!"

        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page()

            # --- 1. Landing page -> reveal the auth tabs -----------------------
            page.goto(URL, timeout=30000)
            # The primary nav button is `st.button("Connexion", ..., key="nav_login")`,
            # a plain button (role="button"). Once revealed there is also a
            # "🔑 Connexion" *tab* (role="tab"), which is a different accessible
            # role, so an exact match on "Connexion" here is unambiguous.
            page.get_by_role("button", name="Connexion", exact=True).click()

            # --- 2. Switch to the registration tab and fill it out -------------
            page.get_by_role("tab", name="Créer un compte").click()

            page.get_by_placeholder("contact@maboutique.com").fill(test_email)
            page.get_by_placeholder("Min. 6 caractères").fill(test_password)
            page.get_by_placeholder("Retapez votre mot de passe").fill(test_password)
            page.get_by_role("checkbox").check()

            page.get_by_role("button", name="Créer mon compte gratuitement").click()

            # --- 3. Registration should redirect straight into onboarding ------
            wait_for_text(page, "Dites-nous qui vous êtes", timeout=30000)

            # --- 4. Log out. Direct query-param navigation (?logout=1&token=<email>)
            #        instead of clicking the custom top-nav logout link, which is
            #        not reliably driven through coordinate-based automation and
            #        is exactly how the app itself expects logout links to work.
            logout_url = f"{URL}/?logout=1&token={urllib.parse.quote(test_email)}"
            page.goto(logout_url, timeout=30000)
            content = page.content()
            assert ('Se connecter' in content) or ("S'inscrire" in content), \
                'Expected to land back on the landing/login page after logout'

            # --- 5. First login with the freshly created account ---------------
            page.get_by_role("button", name="Connexion", exact=True).click()
            page.get_by_placeholder("votre@email.com").fill(test_email)
            page.get_by_placeholder("Votre mot de passe").fill(test_password)
            page.get_by_role("button", name="Se connecter", exact=True).click()

            # Onboarding was never completed during registration, so the first
            # login after registration should land back in the same onboarding
            # wizard rather than surfacing an error.
            wait_for_text(page, "Dites-nous qui vous êtes", timeout=30000)
            content = page.content()
            assert 'incorrect' not in content.lower(), \
                'Login after registration unexpectedly showed an error'

            browser.close()
    finally:
        stop_process(proc, log)
