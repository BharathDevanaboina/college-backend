from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


def test_admin_spa_and_public_firebase_config_are_served() -> None:
    """The browser assets and Firebase client config stay available together."""
    app = create_app(
        Settings(
            app_env="test",
            database_url="sqlite://",
            auth_mode="fake",
            storage_backend="local",
            sheets_backend="fake",
            app_check_enabled=False,
            firebase_web_api_key="public-test-key",
            firebase_web_auth_domain="example.firebaseapp.com",
            firebase_web_app_id="test-app-id",
        )
    )
    client = TestClient(app)

    page = client.get("/admin/")
    assert page.status_code == 200
    assert "College Control" in page.text

    config = client.get("/admin/firebase-config.js")
    assert config.status_code == 200
    assert "public-test-key" in config.text
    assert config.headers["cache-control"] == "no-store"
