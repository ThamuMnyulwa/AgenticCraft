"""Find the Gemini API key: the environment first, then Secret Manager."""

import os

from google.cloud import secretmanager

DEFAULT_SECRET_ID = "gemini-api-key"


def _is_set(value: str | None) -> bool:
    return bool(value) and not value.startswith("your-")


def load_gemini_api_key() -> None:
    """Set GEMINI_API_KEY for google-genai and the MLflow judge.

    A key already in the environment wins (CI secret, or one pasted into .env).
    Otherwise it is read from Secret Manager in GOOGLE_CLOUD_PROJECT.
    """
    if _is_set(os.getenv("GEMINI_API_KEY")):
        return

    project = os.getenv("GOOGLE_CLOUD_PROJECT")
    if not _is_set(project):
        raise SystemExit("Set GEMINI_API_KEY, or GOOGLE_CLOUD_PROJECT to read the key from Secret Manager.")

    secret_id = os.getenv("GEMINI_SECRET_ID", DEFAULT_SECRET_ID)
    client = secretmanager.SecretManagerServiceClient()
    name = client.secret_version_path(project, secret_id, "latest")
    os.environ["GEMINI_API_KEY"] = client.access_secret_version(name=name).payload.data.decode().strip()
