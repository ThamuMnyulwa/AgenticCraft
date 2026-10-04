"""Delete the deployed agent. Run before terraform destroy, since the agent uses the bucket."""

import agentplatform

from part2_agent_platform.settings import AGENT_RESOURCE_FILE, load_settings

if not AGENT_RESOURCE_FILE.exists():
    print("No deployed agent recorded, nothing to delete.")
else:
    settings = load_settings()
    client = agentplatform.Client(project=settings.project, location=settings.region)
    name = AGENT_RESOURCE_FILE.read_text().strip()
    client.runtimes.delete(name=name, force=True)  # force also deletes its sessions
    AGENT_RESOURCE_FILE.unlink()
    print(f"Deleted {name}")
