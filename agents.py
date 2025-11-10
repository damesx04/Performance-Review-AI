from typing import List, Tuple, Any, Optional, Dict, Union
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.runnables import Runnable, RunnableConfig
from langchain_core.callbacks import CallbackManagerForChainRun
from github_tools import GitHubTools
from langchain.tools import StructuredTool

def create_github_tools() -> List[StructuredTool]:
    """Create and return GitHub-related tools."""
    github = GitHubTools()
    
    tools = [
        StructuredTool(
            name="search_all_repositories",
            description="Search for all accessible repositories, optionally filtered by organization",
            func=github.search_all_repositories,
            args_schema={
                "org": {
                    "type": "string",
                    "description": "Optional organization name to filter repositories"
                }
            }
        ),
        StructuredTool(
            name="list_user_commits",
            description="Get all commits by a specific user in a repository",
            func=github.list_user_commits,
            args_schema={
                "repo_name": {
                    "type": "string",
                    "description": "Full name of the repository (e.g., 'owner/repo')"
                },
                "username": {
                    "type": "string",
                    "description": "GitHub username to search commits for"
                }
            }
        ),
        StructuredTool(
            name="get_commit_details",
            description="Get detailed information about a specific commit",
            func=github.get_commit_details,
            args_schema={
                "repo_name": {
                    "type": "string",
                    "description": "Full name of the repository (e.g., 'owner/repo')"
                },
                "commit_sha": {
                    "type": "string",
                    "description": "SHA of the commit to get details for"
                }
            }
        ),
        StructuredTool(
            name="summarize_commit_history",
            description="Generate a summary of commit history with statistics",
            func=github.summarize_commit_history,
            args_schema={
                "commits": {
                    "type": "array",
                    "description": "List of commit dictionaries to summarize"
                }
            }
        )
    ]
    
    return tools

def create_agent(model_name: str, tools: list, memory: Optional[Any] = None) -> Runnable:
    """
    Create an OpenAI agent with the specified tools and memory.
    
    Args:
        model_name (str): The name of the model to use (e.g., 'gpt-4')
        tools (list): List of tools to provide to the agent
        memory: Optional memory object for the agent
        
    Returns:
        Runnable: A runnable chain that processes inputs and returns responses
        
    Raises:
        Exception if agent creation fails
    """
    try:
        # Create a ChatOpenAI model instance
        llm = ChatOpenAI(
            model=model_name,
            temperature=0
        )
        
        # Create the system message for the agent
        system_template = (
            "You are an AI assistant helping with GitHub repositories, Jira issues, "
            "and Confluence pages. You have access to various tools to help with "
            "these tasks. Think through your tasks step by step and use the most "
            "appropriate tools to accomplish them.\n\n"
            "Available tools:\n{tools_desc}\n\n"
            "For GitHub tasks, follow this workflow:\n"
            "1. Use search_all_repositories to find repositories\n"
            "2. Use list_user_commits to get commits from each repository\n"
            "3. Use get_commit_details for detailed commit information\n"
            "4. Use summarize_commit_history to generate the final report\n\n"
            "To use a tool, format your response like this:\n"
            "[TOOL] tool_name\n"
            "tool_input_here\n[/TOOL]\n\n"
            "When you don't need a tool, respond normally."
        )
        
        # Create descriptions of available tools
        tools_desc = "\n".join(f"- {tool.name}: {tool.description}" for tool in tools)
        
        # Create the prompt template with optional chat history
        messages = [("system", system_template)]
        if memory is not None:
            messages.append(MessagesPlaceholder(variable_name="chat_history"))
        messages.append(("human", "{input}"))
        
        prompt = ChatPromptTemplate.from_messages(messages)
        
        async def process_response(response: str) -> Dict[str, Any]:
            """Process the response and execute any tool calls"""
            # Check for tool usage patterns
            if "[TOOL]" in response:
                # Extract tool calls
                parts = response.split("[TOOL]")
                response_text = parts[0].strip()
                
                for part in parts[1:]:
                    if "[/TOOL]" in part:
                        tool_section, after = part.split("[/TOOL]", 1)
                        tool_lines = tool_section.strip().split("\n", 1)
                        if len(tool_lines) == 2:
                            tool_name = tool_lines[0].strip()
                            tool_input = tool_lines[1].strip()
                            
                            # Find and execute the tool
                            for tool in tools:
                                if tool.name.lower() == tool_name.lower():
                                    try:
                                        if hasattr(tool, '_arun'):
                                            tool_result = await tool._arun(tool_input)
                                        else:
                                            tool_result = tool._run(tool_input)
                                        response_text += f"\n\nTool {tool_name} result:\n{tool_result}\n"
                                    except Exception as e:
                                        response_text += f"\n\nError using tool {tool_name}: {str(e)}\n"
                        response_text += after
                
                return {"output": response_text}
            else:
                return {"output": response}
        
        # Create the chain
        chain = (
            {
                "input": lambda x: x,
                "tools_desc": lambda x: tools_desc,
                "chat_history": lambda x: [] if memory is None else memory.messages if hasattr(memory, 'messages') else []
            }
            | prompt 
            | llm
            | process_response
        )
        
        return chain
        
    except Exception as e:
        print(f"Error creating agent: {e}")
        raise