#!/usr/bin/env python3
import argparse
import requests
import sys


def register(server: str, agent_id: str):
    try:
        r = requests.post(f"{server}/mcp/register", params={"agent_id": agent_id}, timeout=5)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print("Register failed:", e, file=sys.stderr)
        return None


def send_content(server: str, agent_id: str, content: str):
    try:
        payload = {"agent_id": agent_id, "content": content}
        r = requests.post(f"{server}/mcp", json=payload, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print("Send failed:", e, file=sys.stderr)
        return None


def main():
    p = argparse.ArgumentParser(description="Simple AgentMink client agent")
    p.add_argument("--server", default="http://localhost:8000", help="MCP server base URL")
    p.add_argument("--agent-id", required=True, help="Agent identifier")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--text", help="Text payload to send")
    g.add_argument("--file", help="Path to file to send")
    args = p.parse_args()

    print("Registering agent...")
    reg = register(args.server, args.agent_id)
    if not reg:
        sys.exit(2)
    print("Registered:", reg)

    if args.file:
        try:
            with open(args.file, "r", errors="ignore") as fh:
                content = fh.read()
        except Exception as e:
            print("Failed to read file:", e, file=sys.stderr)
            sys.exit(3)
    else:
        content = args.text

    print("Sending content to MCP...")
    resp = send_content(args.server, args.agent_id, content)
    print("Response:", resp)


if __name__ == "__main__":
    main()
