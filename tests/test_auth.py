import pytest
from emailer_bot.auth import generate_oauth2_string

def test_generate_oauth2_string():
    username = "user@example.com"
    token = "some_token"
    expected = "user=user@example.com\x01auth=Bearer some_token\x01\x01"
    assert generate_oauth2_string(username, token) == expected
