import asyncio
import os
from langchain_mcp_adapters.client import MultiServerMCPClient
from agents import create_agent
from dotenv import load_dotenv
from typing import Dict, Tuple

load_dotenv()

# Feature weights for different metrics
WEIGHTS = {
    'jira_issues': 0.5,
    'confluence_pages': 0.5,
    'github_commits': 0.5
}

async def init_mcp_client():
    """Initialize MCP client with all required services."""
    return MultiServerMCPClient({
        "github": {
            "url": "https://api.githubcopilot.com/mcp/",
            "transport": "streamable_http",
            "headers": {
                "Authorization": f"Bearer {os.getenv('GITHUB_PERSONAL_ACCESS_TOKEN')}"
            }
        },
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
                "JIRA_URL": "https://ufl-team-xlqau1ra.atlassian.net",
                "JIRA_USERNAME": "damesx@ufl.edu",
                "JIRA_API_TOKEN": os.getenv('JIRA_API_TOKEN'),
                "CONFLUENCE_URL": "https://ufl-team-xlqau1ra.atlassian.net/wiki",
                "CONFLUENCE_USERNAME": "damesx@ufl.edu",
                "CONFLUENCE_API_TOKEN": os.getenv('CONFLUENCE_API_TOKEN')
            },
            "transport": "stdio",
        }   
    })

async def get_jira_completed_issues(agent, username: str) -> int:
    """Get count of completed Jira issues for a user."""
    try:
        response = await agent.ainvoke({
            "messages": [{
                "role": "user",
                "content": f"How many issues has {username} completed in Jira? Only return the number."
            }]
        })
        # Extract the number from the response
        content = response["messages"][-1].content
        # Try to extract just the number from the response
        import re
        numbers = re.findall(r'\d+', content)
        return int(numbers[0]) if numbers else 0
    except Exception as e:
        print(f"Error fetching Jira issues: {e}")
        return 0

async def get_confluence_pages(agent, username: str) -> int:
    """Get count of Confluence pages created by a user."""
    try:
        response = await agent.ainvoke({
            "messages": [{
                "role": "user",
                "content": f"How many pages has {username} created in Confluence? Only return the number."
            }]
        })
        content = response["messages"][-1].content
        # Try to extract just the number from the response
        import re
        numbers = re.findall(r'\d+', content)
        return int(numbers[0]) if numbers else 0
    except Exception as e:
        print(f"Error fetching Confluence pages: {e}")
        return 0

async def get_github_commits(agent, username: str, repository: str = None) -> int:
    """Get count of GitHub commits for a user."""
    try:
        query = f"How many commits has {username} made"
        if repository:
            query += f" in the repository {repository}"
        query += "? Only return the number."

        response = await agent.ainvoke({
            "messages": [{
                "role": "user",
                "content": query
            }]
        })
        content = response["messages"][-1].content
        # Try to extract just the number from the response
        import re
        numbers = re.findall(r'\d+', content)
        return int(numbers[0]) if numbers else 0
    except Exception as e:
        print(f"Error fetching GitHub commits: {e}")
        return 0

def calculate_performance_score(metrics: Dict[str, int]) -> Tuple[float, Dict[str, float]]:
    """Calculate the weighted performance score from the metrics."""
    weighted_scores = {}
    total_score = 0
    
    for metric, value in metrics.items():
        weight = WEIGHTS.get(metric, 0)
        weighted_score = value * weight
        weighted_scores[metric] = weighted_score
        total_score += weighted_score
    
    return total_score, weighted_scores

async def evaluate_performance(username: str, github_repo: str = None) -> Dict:
    """Main function to evaluate performance across all platforms."""
    try:
        # Initialize MCP client and create agent
        client = await init_mcp_client()
        tools = await client.get_tools()
        agent = create_agent('gpt-4', tools=tools)
        
        # Gather metrics
        metrics = {
            'jira_issues': await get_jira_completed_issues(agent, username),
            'confluence_pages': await get_confluence_pages(agent, username),
            'github_commits': await get_github_commits(agent, username, github_repo)
        }
        
        # Calculate performance score
        total_score, weighted_scores = calculate_performance_score(metrics)
        
        # Prepare detailed report
        report = {
            'username': username,
            'raw_metrics': metrics,
            'weighted_scores': weighted_scores,
            'total_score': total_score,
            'weights_used': WEIGHTS
        }
        
        return report
    except Exception as e:
        print(f"Error in performance evaluation: {e}")
        return None
    finally:
        if 'client' in locals():
            await client.close()

async def main():
    """Test function"""
    username = "damesx04"  
    report = await evaluate_performance(username)
    
    if report:
        print("\nPerformance Evaluation Report")
        print("-" * 30)
        print(f"Username: {report['username']}")
        print("\nRaw Metrics:")
        for metric, value in report['raw_metrics'].items():
            print(f"- {metric}: {value}")
        print("\nWeighted Scores:")
        for metric, score in report['weighted_scores'].items():
            print(f"- {metric}: {score:.2f}")
        print(f"\nTotal Performance Score: {report['total_score']:.2f}")
    else:
        print("Failed to generate performance report")

if __name__ == "__main__":
    asyncio.run(main())