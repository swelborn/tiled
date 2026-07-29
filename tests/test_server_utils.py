import pytest
from starlette.requests import Request

from tiled.server.utils import (
    get_current_url,
    get_root_url,
    normalize_root_path,
    strip_root_path,
)


def make_request(path, root_path="", headers=None, scheme="http"):
    headers = headers or {"host": "example.org"}
    return Request(
        {
            "type": "http",
            "scheme": scheme,
            "server": ("example.org", 80),
            "path": path,
            "root_path": root_path,
            "headers": [
                (key.lower().encode(), value.encode()) for key, value in headers.items()
            ],
            "query_string": b"",
        }
    )


@pytest.mark.parametrize(
    "root_path,expected",
    [
        (None, ""),
        ("", ""),
        ("/", ""),
        ("//", ""),
        ("/tiled", "/tiled"),
        ("/tiled/", "/tiled"),
        ("tiled", "/tiled"),
        ("/a/b/", "/a/b"),
        ("/tenant/ui/tiled", "/tenant/ui/tiled"),
    ],
)
def test_normalize_root_path(root_path, expected):
    assert normalize_root_path(root_path) == expected


@pytest.mark.parametrize(
    "path,root_path,expected",
    [
        ("/tiled/api", "/tiled", "/api"),
        ("/tiled", "/tiled", ""),
        ("/tiled/api", "", "/tiled/api"),
        # Only strip on a path-segment boundary, as Starlette's router does.
        ("/tiled/api", "/tile", "/tiled/api"),
        ("/other", "/tiled", "/other"),
    ],
)
def test_strip_root_path(path, root_path, expected):
    assert strip_root_path(path, root_path) == expected


@pytest.mark.parametrize(
    "path,root_path,expected",
    [
        (
            # The ASGI server prepends root_path to path, so root_path must be
            # counted exactly once.
            "/tiled/api/v1/auth/provider/orcid/code",
            "/tiled",
            "http://example.org/tiled/api/v1/auth/provider/orcid/code",
        ),
        (
            "/api/v1/auth/provider/orcid/code",
            "",
            "http://example.org/api/v1/auth/provider/orcid/code",
        ),
    ],
)
def test_get_current_url(path, root_path, expected):
    assert get_current_url(make_request(path, root_path=root_path)) == expected


def test_get_root_url_honors_forwarded_headers():
    request = make_request(
        "/tiled/api/v1",
        root_path="/tiled",
        headers={
            "host": "localhost:8000",
            "x-forwarded-host": "example.com",
            "x-forwarded-proto": "https",
        },
    )
    assert get_root_url(request) == "https://example.com/tiled"
