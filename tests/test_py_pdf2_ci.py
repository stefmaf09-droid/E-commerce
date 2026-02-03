import os
import pytest

CI_IS_GITHUB = os.environ.get("GITHUB_ACTIONS") == "true"

@pytest.mark.skipif(not CI_IS_GITHUB, reason="CI-only smoke test for PyPDF2 presence")
def test_pypdf2_available_in_ci():
    """Smoke test: ensure PyPDF2 is available in CI (fails CI when missing)."""
    try:
        import PyPDF2
    except Exception as e:
        pytest.fail(f"PyPDF2 is not available in CI runner: {e}")

    # Optional: check minimal version
    version = getattr(PyPDF2, '__version__', None)
    assert version is not None and tuple(int(x) for x in version.split('.')[:2]) >= (3, 0), (
        f"PyPDF2 version is too old in CI: {version}. Require >= 3.0.0"
    )
