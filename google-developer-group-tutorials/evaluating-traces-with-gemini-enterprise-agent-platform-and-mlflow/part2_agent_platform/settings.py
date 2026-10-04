"""Read the Terraform outputs so the Python scripts and the Terraform never drift apart."""

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AGENT_RESOURCE_FILE = ROOT / ".agent_resource"


@dataclass
class Settings:
    project: str
    region: str
    bucket: str
    service_account: str


def load_settings() -> Settings:
    raw = subprocess.run(
        ["terraform", f"-chdir={ROOT / 'terraform' / 'agent_platform'}", "output", "-json"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    outputs = {name: item["value"] for name, item in json.loads(raw).items()}
    if not outputs:
        raise SystemExit("No Terraform outputs found. Run ./demo.sh infra-up first.")
    return Settings(
        project=outputs["project_id"],
        region=outputs["region"],
        bucket=outputs["bucket_name"],
        service_account=outputs["agent_service_account_email"],
    )


def load_agent_resource() -> str:
    if not AGENT_RESOURCE_FILE.exists():
        raise SystemExit("No deployed agent found. Run ./demo.sh deploy first.")
    return AGENT_RESOURCE_FILE.read_text().strip()
