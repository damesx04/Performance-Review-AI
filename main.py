import os
import asyncio
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from langchain_mcp_adapters.client import MultiServerMCPClient
from agents import create_agent, create_github_tools
from asyncio import TaskGroup
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
import json
from datetime import datetime

load_dotenv()

# Check required environment variables
required_vars = ['GITHUB_PERSONAL_ACCESS_TOKEN', 'OPENAI_API_KEY', 
                'JIRA_API_TOKEN', 'CONFLUENCE_API_TOKEN']
missing_vars = [var for var in required_vars if not os.getenv(var)]
if missing_vars:
    raise EnvironmentError(f"Missing required environment variables: {', '.join(missing_vars)}")

app = FastAPI()

# global variables
client = None
tools = []
agent = None
memory = None
vectorstore = None

async def init_memory():
    global vectorstore
    # Initialize the vector store
    embeddings = OpenAIEmbeddings()
    vectorstore = Chroma(
        collection_name="chat_history",
        embedding_function=embeddings,
        persist_directory="./data"
    )
    
    # Load existing history if any
    try:
        with open("chat_history.json", "r") as f:
            history = json.load(f)
            texts = []
            metadatas = []
            for entry in history:
                texts.append(entry["content"])
                metadatas.append({
                    "type": entry["role"],
                    "timestamp": entry["timestamp"]
                })
            if texts:
                vectorstore.add_texts(texts=texts, metadatas=metadatas)
    except FileNotFoundError:
        print("No existing chat history found. Starting fresh.")

async def save_to_history(role: str, content: str):
    # Save to JSON file
    try:
        try:
            with open("chat_history.json", "r") as f:
                history = json.load(f)
        except FileNotFoundError:
            history = []
        
        history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        
        with open("chat_history.json", "w") as f:
            json.dump(history, f, indent=2)
        
        # Add to vector store
        if vectorstore:
            vectorstore.add_texts(
                texts=[content],
                metadatas=[{"type": role, "timestamp": datetime.now().isoformat()}]
            )
    except Exception as e:
        print(f"Error saving to history: {e}")

async def init_mcp_client():
    try:
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
                    "JIRA_URL": os.getenv("JIRA_URL"),
                    "JIRA_USERNAME": os.getenv("JIRA_USERNAME"),
                    "JIRA_API_TOKEN": os.getenv("JIRA_API_TOKEN"),
                    "CONFLUENCE_URL": os.getenv("CONFLUENCE_URL"),
                    "CONFLUENCE_USERNAME": os.getenv("CONFLUENCE_USERNAME"),
                    "CONFLUENCE_API_TOKEN": os.getenv("CONFLUENCE_API_TOKEN")
                },
                "transport": "stdio"
            }
        })
    except Exception as e:
        raise Exception(f"Failed to initialize MCP client: {str(e)}")

class ChatRequest(BaseModel):
    message: str

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    global client, agent, tools, memory
    
    if not client:
        print("\nInitializing MCP client...")
        client = await init_mcp_client()
        
        # Get all tools from the client
        client_tools = await client.get_tools()
        print("\nFetched tools from client:", len(client_tools))
        
        # Initialize tools
        tools = client_tools + create_github_tools()
        
        # Initialize the agent with tools and memory
        agent = create_agent("gpt-4", tools=tools, memory=memory)
        
        print("\nAgent initialized successfully")
    
    try:
        # Process the chat request
        response = await agent.ainvoke({
            "input": request.message,
            "chat_history": []  # You can implement chat history here
        })
        
        # Save the interaction to history
        await save_to_history("user", request.message)
        await save_to_history("assistant", response["output"])
        
        return {
            "response": response["output"],
            "status": "success"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.on_event("startup")
async def startup_event():
    global memory
    await init_memory()
    print("Memory system initialized")

@app.on_event("shutdown")
async def shutdown_event():
    global client
    if client:
        try:
            await client.close()
        except:
            pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)