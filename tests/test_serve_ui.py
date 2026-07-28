import re

import pytest
from httpx import ASGITransport, AsyncClient
from starlette.status import HTTP_200_OK

from tiled.server.app import build_app

TILED_INDEX_HTML = (
    '<html><head><base href="/ui/" /></head>'
    '<body><script src="./assets/app.js"></script></body></html>'
)
VENDORED_INDEX_HTML = (
    '<html><head></head><body><script src="./assets/app.js"></script></body></html>'
)


@pytest.fixture
def serve_ui(tmp_path, monkeypatch):
    """Serve `index_html` as the UI distribution and report what a browser gets."""
    (tmp_path / "ui").mkdir()
    (tmp_path / "templates").mkdir()
    (tmp_path / "static").mkdir()
    (tmp_path / "static" / "default_ui_settings.yml").write_text(
        "api_url: /api/v1\nspecs: []\nstructure_families: {}\n"
    )
    monkeypatch.setattr("tiled.server.app.SHARE_TILED_PATH", tmp_path)
    monkeypatch.delenv("TILED_UI_SETTINGS", raising=False)

    async def serve(
        index_html=TILED_INDEX_HTML,
        *,
        configured_root_path="",
        request_root_path="",
        path="/ui/browse/deep/path",
    ):
        (tmp_path / "ui" / "index.html").write_text(index_html)
        app = build_app({}, server_settings={"root_path": configured_root_path})
        transport = ASGITransport(app=app, root_path=request_root_path)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            index = await client.get(path)
            settings = await client.get("/tiled-ui-settings")
        assert index.status_code == HTTP_200_OK
        assert settings.status_code == HTTP_200_OK
        return index.text, settings.json()

    return serve


def base_href(html):
    (href,) = re.findall(r'<base href="([^"]*)"', html)
    return href


@pytest.mark.parametrize(
    "request_root_path,configured_root_path,expected",
    [
        pytest.param("", "", "", id="unmounted"),
        pytest.param("/", "", "", id="trailing-slash-stripped"),
        pytest.param("/tenant/ui/tiled", "", "/tenant/ui/tiled", id="from-request"),
        pytest.param("", "/configured", "/configured", id="from-server-settings"),
        pytest.param("/mounted", "/configured", "/mounted", id="request-wins"),
        pytest.param("/", "/configured", "/configured", id="slash-is-not-an-override"),
    ],
)
@pytest.mark.asyncio
async def test_ui_uses_runtime_root_path(
    serve_ui, request_root_path, configured_root_path, expected
):
    html, settings = await serve_ui(
        configured_root_path=configured_root_path, request_root_path=request_root_path
    )

    assert base_href(html) == f"{expected}/ui/"
    assert settings["api_url"] == f"{expected}/api/v1"
    # Asset URLs stay relative, to be resolved against <base>.
    assert 'src="./assets/app.js"' in html


@pytest.mark.asyncio
async def test_vendored_ui_is_served_verbatim(serve_ui):
    html, _ = await serve_ui(
        VENDORED_INDEX_HTML,
        configured_root_path="/tiled",
        request_root_path="/tiled",
        path="/ui/",
    )

    assert html == VENDORED_INDEX_HTML
