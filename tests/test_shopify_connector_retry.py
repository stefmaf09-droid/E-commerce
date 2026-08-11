"""
Unit tests for the retry/backoff behaviour added to ShopifyConnector._get()
(see docs/ROADMAP.md, priorite haute item 3 : "Retrys & Idempotence - Shopify connector").

These tests mock requests.Session.get so they run instantly (time.sleep is
patched out) and never hit the real Shopify API.
"""
import os
import sys
from unittest.mock import MagicMock, patch

import pytest
import requests

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.integrations.shopify_connector import ShopifyConnector, ShopifyRateLimitError


def make_connector():
    return ShopifyConnector({
        "shop_domain": "test-shop",
        "access_token": "fake-token",
    })


@patch("time.sleep", return_value=None)  # skip real backoff delays in tests
def test_get_retries_on_429_then_succeeds(mock_sleep):
    connector = make_connector()

    rate_limited_response = MagicMock()
    rate_limited_response.status_code = 429
    rate_limited_response.headers = {"Retry-After": "1"}

    success_response = MagicMock()
    success_response.status_code = 200
    success_response.headers = {}
    success_response.raise_for_status = MagicMock()

    connector.session.get = MagicMock(side_effect=[rate_limited_response, success_response])

    result = connector._get(f"{connector.base_url}/shop.json")

    assert result is success_response
    assert connector.session.get.call_count == 2


@patch("time.sleep", return_value=None)
def test_get_retries_on_connection_error_then_succeeds(mock_sleep):
    connector = make_connector()

    success_response = MagicMock()
    success_response.status_code = 200
    success_response.headers = {}

    connector.session.get = MagicMock(
        side_effect=[requests.exceptions.ConnectionError("boom"), success_response]
    )

    result = connector._get(f"{connector.base_url}/shop.json")

    assert result is success_response
    assert connector.session.get.call_count == 2


@patch("time.sleep", return_value=None)
def test_get_gives_up_after_max_tries_on_persistent_429(mock_sleep):
    connector = make_connector()

    rate_limited_response = MagicMock()
    rate_limited_response.status_code = 429
    rate_limited_response.headers = {"Retry-After": "1"}

    # Always rate-limited: backoff should give up after max_tries=4 and
    # surface the ShopifyRateLimitError rather than retrying forever.
    connector.session.get = MagicMock(return_value=rate_limited_response)

    with pytest.raises(ShopifyRateLimitError):
        connector._get(f"{connector.base_url}/shop.json")

    assert connector.session.get.call_count == 4


@patch("time.sleep", return_value=None)
def test_authenticate_uses_retrying_get(mock_sleep):
    connector = make_connector()
    ok_response = MagicMock()
    ok_response.status_code = 200
    ok_response.headers = {}
    ok_response.raise_for_status = MagicMock()
    connector.session.get = MagicMock(return_value=ok_response)

    assert connector.authenticate() is True
