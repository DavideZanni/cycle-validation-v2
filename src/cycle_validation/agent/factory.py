"""Quale sessione usare, dalle impostazioni (`agent.session_backend`, MG54)."""

from pathlib import Path

from cycle_validation.agent.session import AgentSession
from cycle_validation.config import AgentSettings


def make_agent_session(
    settings: AgentSettings, transcripts_dir: Path | None = None
) -> AgentSession:
    if settings.session_backend == "diretta":
        from cycle_validation.agent.direct_session import DirectBedrockSession

        return DirectBedrockSession(settings, transcripts_dir)
    from cycle_validation.agent.sdk_session import SdkAgentSession

    return SdkAgentSession(settings, transcripts_dir)
