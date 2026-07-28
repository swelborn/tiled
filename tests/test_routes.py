import pytest
from httpx import ASGITransport, AsyncClient
from starlette.status import HTTP_200_OK

from tiled.server.app import build_app


@pytest.mark.parametrize("path", ["/", "/docs", "/healthz"])
@pytest.mark.asyncio
async def test_meta_routes(path):
    transport = ASGITransport(app=build_app({}))
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(path)
    assert response.status_code == HTTP_200_OK


@pytest.fixture
def ui_share(tmp_path, monkeypatch):
    (tmp_path / "ui").mkdir()
    (tmp_path / "ui" / "index.html").write_text(
        "<html><head>"
        '<base href="{{ tiled_runtime_base }}" />'
        '<script type="application/json" id="tiled-runtime-config">'
        "{{ tiled_runtime_config }}</script>"
        '</head><body><script src="./assets/app.js"></script></body></html>'
    )
    (tmp_path / "static").mkdir()
    (tmp_path / "static" / "default_ui_settings.yml").write_text(
        "api_url: /api/v1\nspecs: []\nstructure_families: {}\n"
    )
    (tmp_path / "templates").mkdir()
    monkeypatch.setattr("tiled.server.app.SHARE_TILED_PATH", tmp_path)
    monkeypatch.delenv("TILED_UI_SETTINGS", raising=False)


@pytest.mark.parametrize(
    "request_root_path,configured_root_path,expected_root_path",
    [
        ("", "", ""),
        ("/", "", ""),
        ("/tenant/ui/tiled", "", "/tenant/ui/tiled"),
        ("", "/configured", "/configured"),
        ("/mounted", "/configured", "/mounted"),
    ],
)
@pytest.mark.asyncio
async def test_ui_uses_runtime_root_path(
    ui_share, request_root_path, configured_root_path, expected_root_path
):
    app = build_app({}, server_settings={"root_path": configured_root_path})
    transport = ASGITransport(app=app, root_path=request_root_path)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        index_response = await client.get("/ui/browse/deep/path")
        settings_response = await client.get("/tiled-ui-settings")

    assert index_response.status_code == HTTP_200_OK
    assert f'<base href="{expected_root_path}/ui/" />' in index_response.text
    assert (
        f'{{"root_path": "{expected_root_path}", '
        f'"api_url": "{expected_root_path}/api/v1"}}' in index_response.text
    )
    assert 'src="./assets/app.js"' in index_response.text
    assert settings_response.json()["api_url"] == f"{expected_root_path}/api/v1"


@pytest.mark.asyncio
async def test_ui_without_template_variables_is_untouched(tmp_path, monkeypatch):
    # A custom/vendored frontend that declares none of Tiled's template
    # variables must be served byte-for-byte, with no <base> tag injected.
    original_html = (
        '<html><head></head><body><script src="./assets/app.js"></script></body></html>'
    )
    (tmp_path / "ui").mkdir()
    (tmp_path / "ui" / "index.html").write_text(original_html)
    (tmp_path / "static").mkdir()
    (tmp_path / "static" / "default_ui_settings.yml").write_text(
        "api_url: /api/v1\nspecs: []\nstructure_families: {}\n"
    )
    (tmp_path / "templates").mkdir()
    monkeypatch.setattr("tiled.server.app.SHARE_TILED_PATH", tmp_path)
    monkeypatch.delenv("TILED_UI_SETTINGS", raising=False)

    app = build_app({}, server_settings={"root_path": "/tiled"})
    transport = ASGITransport(app=app, root_path="/tiled")
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/ui/")

    assert response.status_code == HTTP_200_OK
    assert response.text == original_html
    assert "<base" not in response.text
