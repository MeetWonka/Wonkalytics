from analytics import score
import pytest

def test_write_to_azure_sql():
    response_id = "chatcmpl-8jnIJAkEKBQJn5cs7QCJ1wIcBaII2"
    assert score(response_id, 100) == True  # Returns true if no errors

