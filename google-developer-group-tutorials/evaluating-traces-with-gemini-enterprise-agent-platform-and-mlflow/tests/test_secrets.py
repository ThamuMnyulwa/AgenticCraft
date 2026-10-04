import pytest

from shared import secrets


class FakeClient:
    secret_version_path = staticmethod(lambda project, secret, version: f"{project}/{secret}/{version}")

    def access_secret_version(self, name):
        assert name == "my-project/gemini-api-key/latest"
        payload = type("Payload", (), {"data": b"key-from-secret-manager\n"})
        return type("Response", (), {"payload": payload})


def test_environment_key_wins(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "key-from-env")
    monkeypatch.setattr(secrets.secretmanager, "SecretManagerServiceClient", pytest.fail)
    secrets.load_gemini_api_key()
    assert secrets.os.environ["GEMINI_API_KEY"] == "key-from-env"


def test_reads_secret_manager_when_env_is_empty(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "")
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "my-project")
    monkeypatch.delenv("GEMINI_SECRET_ID", raising=False)
    monkeypatch.setattr(secrets.secretmanager, "SecretManagerServiceClient", FakeClient)
    secrets.load_gemini_api_key()
    assert secrets.os.environ["GEMINI_API_KEY"] == "key-from-secret-manager"


def test_placeholder_project_is_an_error(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "your-gemini-api-key")
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "your-project-id")
    with pytest.raises(SystemExit):
        secrets.load_gemini_api_key()
