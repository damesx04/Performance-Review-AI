import asyncio
import os
import re
import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient
from agents import create_agent
from dotenv import load_dotenv
from custom_tools import (
    SearchRepositoriesTool,
    ListUserCommitsTool,
    GetCommitDetailsTool,
    SummarizeCommitHistoryTool
)

load_dotenv()

async def analyze_github_contributions(username: str, client) -> dict:
    """Analyze GitHub contributions for a specific user."""
    try:
        search_repositories_tool = SearchRepositoriesTool(client)
        list_user_commits_tool = ListUserCommitsTool(client)
        get_commit_details_tool = GetCommitDetailsTool(client)
        summarize_history_tool = SummarizeCommitHistoryTool(client)

        print(f"\nAnalyzing GitHub commit history for {username}...")
        
        # 1. Find repositories
        print("Finding repositories...")
        repos = await search_repositories_tool._arun(username)
        print(f"Found {len(repos)} repositories")

        # 2. Get commit SHAs for each repo
        print("\nGathering commits...")
        all_commits = []
        for repo in repos:
            if repo["full_name"] != f"{username}/{username}":  # Skip profile repo
                owner, repo_name = repo["full_name"].split('/')
                try:
                    commits = await list_user_commits_tool._arun(owner, repo_name, username)
                    all_commits.extend(commits)
                    print(f"Found {len(commits)} commits in {repo['full_name']}")
                except Exception as e:
                    print(f"Error processing {repo['full_name']}: {e}")

        # Debug: Print all_commits format
        print(f"\nDEBUG - all_commits format:")
        print(f"Total commits: {len(all_commits)}")
        if all_commits:
            print(f"First commit: {all_commits[0]}")
            print(f"Commit keys: {list(all_commits[0].keys())}")
            import json
            print("Sample commits (first 3):")
            print(json.dumps(all_commits[:3], indent=2))

        # 3. Get detailed commit info
        print(f"\nGetting detailed information for {len(all_commits)} commits...")
        detailed_commits = []
        for commit in all_commits:
            owner, repo = commit["repository"].split('/')
            try:
                details = await get_commit_details_tool._arun(owner, repo, commit["sha"])
                detailed_commits.append(details)
            except Exception as e:
                print(f"Error getting details for commit {commit['sha']}: {e}")

        # 4. Generate and return summary
        print("\nGenerating summary...")
        return await summarize_history_tool._arun(detailed_commits)
    except Exception as e:
        raise Exception(f"Error analyzing GitHub contributions: {e}")

async def test_github_server(prompt: str = None):
    """Main function that processes different GitHub-related operations based on the prompt."""
    client = None
    
    async def create_new_client():
        return MultiServerMCPClient({
            "github": {
                "url": "https://api.githubcopilot.com/mcp/",
                "transport": "streamable_http",
                "headers": {
                    "Authorization": f"Bearer {os.getenv('GITHUB_PERSONAL_ACCESS_TOKEN')}"
                }
            }
        })

    async def handle_closed_connection():
        nonlocal client
        client = await create_new_client()
        tools = await client.get_tools()
        return create_agent("gpt-4", tools=tools)

    async def safe_query(agent, messages, retry_count=0, max_retries=3, base_wait=0.5):
        try:
            return await agent.ainvoke({"messages": messages})
        except Exception as e:
            error_str = str(e)
            
            if retry_count >= max_retries:
                raise
            
            wait_time = base_wait
            if "rate_limit_exceeded" in error_str:
                # Try to extract wait time from error message
                wait_match = re.search(r'try again in (\d+)ms', error_str)
                if wait_match:
                    wait_ms = int(wait_match.group(1))
                    wait_time = (wait_ms / 1000.0) + 0.1  # Convert to seconds and add small buffer
            
            await asyncio.sleep(wait_time)
            
            if "ClosedResourceError" in error_str:
                agent = await handle_closed_connection()
            
            return await safe_query(agent, messages, retry_count + 1, max_retries, wait_time * 2)

    
    try:
        client = await create_new_client()
        
        # If no prompt is provided, initialize client and return
        if not prompt:
            return True
            
        # Parse the prompt to determine the operation
        prompt_lower = prompt.lower()
        
        # Check if this is a request for commit history analysis
        if any(word in prompt_lower for word in ["commit", "contribution", "history"]):
            # Extract username from prompt or use default
            import re
            username_match = re.search(r'for (\w+)', prompt_lower)
            username = username_match.group(1) if username_match else "damesx04"
            
            # Perform the analysis
            summary = await analyze_github_contributions(username, client)
            
            # Display results
            print("\nAnalysis Results:")
            print("-" * 50)
            print(f"Total Repositories: {summary['total_repositories']}")
            print(f"Total Commits: {summary['total_commits']}")
            print(f"Lines Added: {summary['total_additions']}")
            print(f"Lines Deleted: {summary['total_deletions']}")
            print("\nActivity by Repository:")
            for repo, count in summary['repositories'].items():
                print(f"- {repo}: {count} commits")
            if summary['date_range']['first_commit']:
                print(f"\nFirst Commit: {summary['date_range']['first_commit']}")
                print(f"Last Commit: {summary['date_range']['last_commit']}")
            print("-" * 50)
        else:
            pass
            
        return True

    except Exception as e:
        return False

if __name__ == "__main__":
    import sys
    prompt = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else None
    result = asyncio.run(test_github_server(prompt))
    print(f"Github server: {'✓' if result else '✗'}")