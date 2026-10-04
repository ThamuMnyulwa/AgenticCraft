"""Deploy the ADK agent to Agent Runtime with Cloud Trace telemetry turned on."""

import subprocess
import sys

import agentplatform
from agentplatform.frameworks import AdkApp

from part2_agent_platform.agent.agent import root_agent
from part2_agent_platform.settings import AGENT_RESOURCE_FILE, load_settings


def locked_requirements() -> list[str]:
    """The agent-runtime dependency group, pinned exactly as in uv.lock."""
    exported = subprocess.run(
        [
            "uv",
            "export",
            "--only-group",
            "agent-runtime",
            "--frozen",
            "--no-hashes",
            "--no-header",
            "--no-annotate",
        ],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    return [line.strip() for line in exported.splitlines() if line.strip() and not line.startswith("#")]


settings = load_settings()
client = agentplatform.Client(project=settings.project, location=settings.region)

remote_agent = client.runtimes.create(
    agent=AdkApp(agent=root_agent),
    config={
        "display_name": "devfest-travel-assistant",
        "staging_bucket": f"gs://{settings.bucket}",
        "service_account": settings.service_account,
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}",
        # Every package pinned from uv.lock, so the cloud runs exactly what we tested.
        "requirements": locked_requirements(),
        # Our own code, uploaded next to the agent.
        "extra_packages": ["shared", "part2_agent_platform"],
        # Turns on Cloud Trace and Cloud Logging for the deployed agent.
        "env_vars": {"GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY": "true"},
    },
)

resource_name = remote_agent.api_resource.name
AGENT_RESOURCE_FILE.write_text(resource_name)
print(f"Deployed: {resource_name}")
print(f"Saved to {AGENT_RESOURCE_FILE.name}")
print(f"Agents in the console: https://console.cloud.google.com/vertex-ai/agents?project={settings.project}")
