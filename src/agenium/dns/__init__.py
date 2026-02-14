"""DNS resolution for agent:// URIs."""

from .resolver import DNSResolver, ResolvedAgent, AgentTool, DNSError

__all__ = ["DNSResolver", "ResolvedAgent", "AgentTool", "DNSError"]
