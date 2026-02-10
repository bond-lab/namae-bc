"""Response time tests — verify each route responds within an acceptable time."""

import time
import pytest


@pytest.mark.slow
@pytest.mark.parametrize("url,max_seconds", [
    ('/', 2),
    ('/names.html', 5),
    ('/phenomena/diversity.html', 2),
    ('/phenomena/androgyny.html', 5),
    ('/overlap.html', 5),
    ('/phenomena/topnames.html', 5),
    ('/irregular.html', 10),
    ('/kanji?kanji=美', 5),
])
def test_response_time(client, url, max_seconds):
    start = time.time()
    resp = client.get(url)
    elapsed = time.time() - start
    assert resp.status_code == 200
    assert elapsed < max_seconds, f"{url} took {elapsed:.1f}s (max {max_seconds}s)"
