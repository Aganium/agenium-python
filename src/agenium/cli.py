"""
AGENIUM CLI

Simple command-line interface for agent operations.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys

from . import __version__
from .core.types import parse_agent_uri, validate_agent_name
from .dns.resolver import DNSResolver


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="agenium",
        description="AGENIUM — Agent-to-Agent Communication SDK",
    )
    parser.add_argument("--version", action="version", version=f"agenium {__version__}")

    sub = parser.add_subparsers(dest="command")

    # resolve
    resolve_p = sub.add_parser("resolve", help="Resolve an agent:// URI")
    resolve_p.add_argument("name", help="Agent name or URI (e.g. my-agent or agent://my-agent)")
    resolve_p.add_argument("--server", default="185.204.169.26", help="DNS server")
    resolve_p.add_argument("--port", type=int, default=3000, help="DNS port")

    # validate
    validate_p = sub.add_parser("validate", help="Validate an agent name or URI")
    validate_p.add_argument("name", help="Agent name or URI to validate")

    # status
    sub.add_parser("status", help="Show SDK status")

    args = parser.parse_args()

    if args.command == "resolve":
        asyncio.run(_resolve(args))
    elif args.command == "validate":
        _validate(args)
    elif args.command == "status":
        _status()
    else:
        parser.print_help()


async def _resolve(args: argparse.Namespace) -> None:
    resolver = DNSResolver(server=args.server, port=args.port)
    try:
        agent = await resolver.resolve(args.name)
        print(json.dumps({
            "name": agent.name,
            "uri": agent.uri,
            "endpoint": agent.endpoint,
            "public_key": agent.public_key,
            "tools": [{"name": t.name, "description": t.description} for t in agent.tools],
            "capabilities": agent.capabilities,
            "ttl": agent.ttl,
        }, indent=2))
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def _validate(args: argparse.Namespace) -> None:
    name = args.name
    if name.startswith("agent://"):
        result = parse_agent_uri(name)
        if result:
            print(f"✓ Valid URI: agent://{result}")
        else:
            print(f"✗ Invalid URI: {name}")
            sys.exit(1)
    else:
        if validate_agent_name(name):
            print(f"✓ Valid name: {name} → agent://{name}")
        else:
            print(f"✗ Invalid name: {name}")
            sys.exit(1)


def _status() -> None:
    print(f"AGENIUM SDK v{__version__} (Python)")
    print(f"DNS Server: 185.204.169.26:3000")
    print(f"Protocol: agent://")
    print(f"Transport: HTTP/2 + mTLS")
    print(f"Docs: https://docs.agenium.net")


if __name__ == "__main__":
    main()
