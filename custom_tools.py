from typing import List, Dict
from datetime import datetime
from langchain.tools import BaseTool

from typing import Any

class SearchRepositoriesTool(BaseTool):
    name: str = "search_all_repositories"
    description: str = "Searches for all repositories for a given username and returns them as a list"
    client: Any = None
    
    def __init__(self, client):
        super().__init__()
        self.client = client
        
    def _run(self, *args: Any, **kwargs: Any) -> Any:
        """Sync version - not supported"""
        raise NotImplementedError("This tool only supports async execution")
    
    async def _arun(self, username: str) -> List[Dict]:
        try:
            tools = await self.client.get_tools()
            search_tool = next((tool for tool in tools if tool.name == "search_repositories"), None)
            if not search_tool:
                raise Exception("search_repositories tool not found")
            
            result = await self.client.invoke_tool(search_tool, {"query": f"user:{username}"})
            if isinstance(result, dict) and "items" in result:
                repos = [
                    {
                        "name": repo["name"],
                        "full_name": repo["full_name"],
                        "private": repo.get("private", False),
                        "description": repo.get("description", ""),
                        "created_at": repo.get("created_at"),
                        "updated_at": repo.get("updated_at")
                    }
                    for repo in result["items"]
                ]
                return repos
            return []
        except Exception as e:
            raise Exception(f"Error searching repositories: {e}")
    
    def _run(self):
        raise NotImplementedError("This tool only supports async execution")

class ListUserCommitsTool(BaseTool):
    name: str = "list_user_commits"
    description: str = "Gets a list of all commits made by a user in a specific repository"
    client: Any = None
    
    def __init__(self, client):
        super().__init__()
        self.client = client
    
    def _run(self, *args: Any, **kwargs: Any) -> Any:
        """Sync version - not supported"""
        raise NotImplementedError("This tool only supports async execution")
    
    async def _arun(self, owner: str, repo: str, username: str) -> List[Dict]:
        try:
            tools = await self.client.get_tools()
            list_commits_tool = next((tool for tool in tools if tool.name == "list_commits"), None)
            if not list_commits_tool:
                raise Exception("list_commits tool not found")
            
            result = await self.client.invoke_tool(list_commits_tool, {
                "owner": owner,
                "repo": repo,
                "author": username
            })
            
            if isinstance(result, list):
                return [{"sha": commit["sha"], "repository": f"{owner}/{repo}"} for commit in result]
            return []
            
        except Exception as e:
            raise Exception(f"Error listing commits: {e}")

class GetCommitDetailsTool(BaseTool):
    name: str = "get_commit_details"
    description: str = "Gets detailed information about a specific commit"
    client: Any = None
    
    def __init__(self, client):
        super().__init__()
        self.client = client
        
    def _run(self, *args: Any, **kwargs: Any) -> Any:
        """Sync version - not supported"""
        raise NotImplementedError("This tool only supports async execution")
    
    async def _arun(self, owner: str, repo: str, commit_sha: str) -> Dict:
        try:
            tools = await self.client.get_tools()
            get_commit_tool = next((tool for tool in tools if tool.name == "get_commit"), None)
            if not get_commit_tool:
                raise Exception("get_commit tool not found")
            
            result = await self.client.invoke_tool(get_commit_tool, {
                "owner": owner,
                "repo": repo,
                "ref": commit_sha
            })
            
            return {
                "sha": result["sha"],
                "message": result.get("commit", {}).get("message", ""),
                "author": result.get("commit", {}).get("author", {}).get("name", ""),
                "date": result.get("commit", {}).get("author", {}).get("date", ""),
                "url": result.get("html_url", ""),
                "repository": f"{owner}/{repo}",
                "files_changed": result.get("files", []),
                "additions": result.get("stats", {}).get("additions", 0),
                "deletions": result.get("stats", {}).get("deletions", 0)
            }
            
        except Exception as e:
            raise Exception(f"Error getting commit details: {e}")

class SummarizeCommitHistoryTool(BaseTool):
    name: str = "summarize_commit_history"
    description: str = "Analyzes and summarizes a user's commit history across repositories"
    client: Any = None
    
    def __init__(self, client):
        super().__init__()
        self.client = client
        
    def _run(self, *args: Any, **kwargs: Any) -> Any:
        """Sync version - not supported"""
        raise NotImplementedError("This tool only supports async execution")
    
    async def _arun(self, commits: List[Dict]) -> Dict:
        try:
            # Group commits by repository
            repos = {}
            for commit in commits:
                repo = commit["repository"]
                if repo not in repos:
                    repos[repo] = []
                repos[repo].append(commit)
            
            # Calculate statistics
            total_commits = len(commits)
            total_additions = sum(c.get("additions", 0) for c in commits)
            total_deletions = sum(c.get("deletions", 0) for c in commits)
            
            # Analyze commit patterns
            commit_dates = [datetime.fromisoformat(c["date"].replace('Z', '+00:00')) 
                          for c in commits if "date" in c]
            date_range = {
                "first_commit": min(commit_dates).isoformat() if commit_dates else None,
                "last_commit": max(commit_dates).isoformat() if commit_dates else None
            }
            
            return {
                "total_repositories": len(repos),
                "total_commits": total_commits,
                "total_additions": total_additions,
                "total_deletions": total_deletions,
                "date_range": date_range,
                "repositories": {
                    repo: len(commits) for repo, commits in repos.items()
                }
            }
            
        except Exception as e:
            raise Exception(f"Error summarizing commits: {e}")
            
        except Exception as e:
            raise Exception(f"Error getting commits: {e}")
    
    def _run(self):
        raise NotImplementedError("This tool only supports async execution")
