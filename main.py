from dotenv import load_dotenv
from contextlib import AsyncExitStack
from typing import Optional
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from agent import Agent
import os 

load_dotenv()

api_key=os.environ.get("GEMINI_KEY")

class MCP_CLIENT:
    def __init__(self) -> None:
        
        self.session: Optional[ClientSession] = None
        self.exit= AsyncExitStack()
        self.agent=Agent(api_key)

    async def connect_mcp_server(self,server_script_path):
        is_python = server_script_path.endswith('.py')
        is_js = server_script_path.endswith('.js')
        if not (is_python or is_js):
            raise ValueError("Server script must be a .py or .js file")

        cmd="python" if is_python else "node"
        server=await self.exit.enter_async_context(
            stdio_client(
                StdioServerParameters(
                    command=cmd,
                    args=[server_script_path],
                    env=None,
                )
            )
        )
        self.stdio,self.write=server
        self.session = await self.exit.enter_async_context(ClientSession(self.stdio, self.write))
        await self.session.initialize()
        response = await self.session.list_tools()
        tools = [{
        "name": tool.name,
        "description": tool.description,
        "input_schema": tool.inputSchema
        } for tool in response.tools
        ]
        self.agent.tools=tools
        print("\nConnected to server with tools:", [tool["name"] for tool in tools])

    async def get_response(self,input:str):
        try:
            response=self.agent.process_query(input)
            print(response)
            self.agent.history.append({"role": "user", "content": input})
            
            
            if isinstance(response, dict) and response.get("needs_tool", False):
                tool_name = response.get("tool_name", None)
                if tool_name:
                    
                    tool_response=self.agent.process_use_tool(tool_name)
                    
                    self.agent.history.append({"role": "assistant", "content": tool_response})
                    
                    tool=tool_response["tool_name"]
                    
                    call_tool=self.agent.process_use_tool(tool)
                    
                    self.agent.history.append({"role": "process_tool_call", "content": call_tool})
                    
                    result=await self.session.call_tool(tool,call_tool["input"]) 
                    
                    self.agent.history.append({"role": "tool_call_result", "content": result})
                if  isinstance(response, dict) and response.get("direct_response", False):
                    self.agent.history.append({"role": "assistant", "content": response["direct_response"]})

                    final_response=self.agent.generate_response(f"""
                    You are a final response generator.
                    You are giving a conversation history between a chatbot and a user and inside this conversation history lies processes like tool calls and results of tool calls.
                    You are to use the result of the tool call to generate a final response for the user.
                    You are to only generate the final response for the user.
                    You are to not generate any other text.
                    You are to not generate any tool calls.
                    The conversation history is as follows:
                    {self.agent.history}
                    """)
                    return final_response
            else:
                response_text = self.agent.generate_response(input)
                self.agent.history.append({"role": "assistant", "content": response_text})
                return response_text
        except Exception as e:
            return f"An error occurred while processing your request: {str(e)}"
        

            
    async def chat_loop(self):
        """Main chat loop for interacting with the MCP server"""
        print("Chat session started. Type 'exit' to quit.")
        
        while True:
            try:
                user_input = input("\nYou: ").strip()
                
                if user_input.lower() == 'exit':
                    print("Ending chat session...")
                    break
                
                if not user_input:
                    continue
                try:
                 response = await self.get_response(user_input)
                except Exception as e:
                    print(f"\nError occurred: {str(e)}")
                    continue
                if response:
                    print("\nAssistant:", response)
                    
            except Exception as e:
                print(f"\nError occurred: {str(e)}")
                continue

    async def close(self):
        await self.exit.aclose()


async def main():
    mcp_client = MCP_CLIENT()
    server_path=input("Enter the path to the server script: ")
    try:
     await mcp_client.connect_mcp_server(server_path)
     await mcp_client.chat_loop()
    finally:   
      await mcp_client.close()
if __name__ == "__main__":
    import asyncio
    asyncio.run(main())