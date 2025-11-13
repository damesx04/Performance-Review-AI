#!/usr/bin/env python3
import asyncio
import os
from langchain_mcp_adapters.client import MultiServerMCPClient
from agents import create_agent
from dotenv import load_dotenv

load_dotenv()

async def test_jira_server():
    print("Testing JIRA Server...")
    client = MultiServerMCPClient({
        "mcp-atlassian": {
            "command": "docker",
            "args": [
                "run",
                "-i",
                "--rm",
                "-e", "JIRA_URL",
                "-e", "JIRA_USERNAME", 
                "-e", "JIRA_API_TOKEN",
                "-e", "CONFLUENCE_URL",
                "-e", "CONFLUENCE_USERNAME",
                "-e", "CONFLUENCE_API_TOKEN",
                "ghcr.io/sooperset/mcp-atlassian:latest"
            ],
            "env": {
                "JIRA_URL": os.getenv("JIRA_URL"),
                "JIRA_USERNAME": os.getenv("JIRA_USERNAME"),
                "JIRA_API_TOKEN": os.getenv("JIRA_API_TOKEN"),
                "CONFLUENCE_URL": os.getenv("CONFLUENCE_URL"),
                "CONFLUENCE_USERNAME": os.getenv("CONFLUENCE_USERNAME"),
                "CONFLUENCE_API_TOKEN": os.getenv("CONFLUENCE_API_TOKEN")
            },
            "transport": "stdio",
        }
    })
    
    try:
        #await client.initialize()
        tools = await client.get_tools()
        
        # Get all tools and print in a single line
        tool_names = sorted([t.name for t in tools])
        print(f"\nTotal Atlassian tools available: {len(tools)}")
        print("Available tools:", ", ".join(tool_names))
        
        agent = create_agent("gpt-4", tools=tools)

        response = await agent.ainvoke(
            {"messages": [{"role": "user", "content": "List all spaces in Confluence"}]}
        )

        print("\nTest Query Response:")
        print("-" * 30)
        print(response["messages"][-1].content)

        return True
    except Exception as e:
        print(f"JIRA server error: {e}")    
        return False
    finally:
        try:
            await client.close()
        except:
            pass

async def main():
    jira_ok = await test_jira_server()
    
    print(f"\nResults:")
    print(f"JIRA server: {'✓' if jira_ok else '✗'}")

if __name__ == "__main__":
    asyncio.run(main())