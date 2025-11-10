import asyncio
import aiohttp
import os

async def chat_with_agent():
    async with aiohttp.ClientSession() as session:
        print("Chat with AI Agent (type 'exit' to quit)\n")
        
        while True:
            # Get user input
            user_message = input("You: ")
            
            if user_message.lower() == 'exit':
                break
            
            try:
                # Send request to FastAPI server
                async with session.post(
                    "http://localhost:8080/chat",
                    json={"message": user_message}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        print("\nAI:", data["response"])
                        print()  # Empty line for readability
                    else:
                        print(f"\nError: Server returned status {response.status}")
                        print(f"Response: {await response.text()}\n")
            
            except aiohttp.ClientError as e:
                print(f"\nConnection Error: {str(e)}")
                print("Make sure the FastAPI server is running (python main.py)\n")
            except Exception as e:
                print(f"\nError: {str(e)}\n")

if __name__ == "__main__":
    try:
        asyncio.run(chat_with_agent())
    except KeyboardInterrupt:
        print("\nGoodbye!")