from typing import List, Tuple, Any, Optional, Dict, Union
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder, PromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.runnables import Runnable, RunnableConfig
from langchain_core.callbacks import CallbackManagerForChainRun
from langchain.agents import create_react_agent, AgentExecutor

def create_agent(model_name: str, tools: list, memory: Optional[Any] = None):
    """
    Create an OpenAI agent with the specified tools and memory using LangChain's create_react_agent.
    
    Args:
        model_name (str): The name of the model to use (e.g., 'gpt-4')
        tools (list): List of tools to provide to the agent
        memory: Optional memory object for the agent
        
    Returns:
        AgentExecutor: The created agent executor
        
    Raises:
        Exception if agent creation fails
    """
    try:
        # Create a ChatOpenAI model instance
        llm = ChatOpenAI(
            model_name=model_name,
            temperature=0
        )
        
        # Create the system message for the agent
        system_message = SystemMessage(
            content=(
                "You are an AI assistant helping with GitHub repositories, Jira issues, "
                "and Confluence pages. You have access to various tools to help with "
                "these tasks. Think through your tasks step by step and use the most "
                "appropriate tools to accomplish them."
            )
        )
        
        # Create a simple prompt template with the required fields for create_react_agent
        prompt = ChatPromptTemplate.from_template(
            system_message.content + "\n\n{tools}\n\n{tool_names}\n\n{input}\n{agent_scratchpad}"
        )
        
        # Create the agent using create_react_agent
        agent = create_react_agent(llm, tools, prompt)
        
        # Wrap with AgentExecutor
        agent_executor = AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=True,
            max_iterations=5,
            handle_parsing_errors=True,
            memory=memory
        )
        
        return agent_executor
        
    except Exception as e:
        raise Exception(f"Failed to create agent: {str(e)}")

def create_github_tools() -> List:
    """
    Create and return GitHub-related tools.
    This is a placeholder for future GitHub tool integration.
    """
    return []