from dotenv import load_dotenv
from contextlib import AsyncExitStack
from typing import Optional
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from agent import Agent
load_dotenv()

class MCP_CLIENT:
    def __init__(self) -> None:
        
        self.session: Optional[ClientSession] = None
        self.exit= AsyncExitStack()
        self.agent=Agent(None)

    async def connect_mcp_server(self):
        is_python = server_script_path.endswith('.py')
        is_js = server_script_path.endswith('.js')
        if not (is_python or is_js):
            raise ValueError("Server script must be a .py or .js file")

        cmd="python" if is_python else "node"
        server=await self.exit.enter_async_context(
            stdio_client(
                StdioServerParameters(
                    cmd=cmd,
                    args=[server_script_path],
                    env=None,
                )
            )
        )
        self.stdio,self.write=server
        self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))
        await self.session.initialize()
        response = await self.session.list_tools()
        tools = [{
        "name": tool.name,
        "description": tool.description,
        "input_schema": tool.inputSchema
        } for tool in response.tools
        ]
        self.agent.tools=tools
        print("\nConnected to server with tools:", [tool.name for tool in tools])

    async def get_response(self,input:str):
        response_history=[]
        response=self.agent.process_query(input)
        response_history.append({"role": "user", "content": input})
        if response.needs_tool==True:
            tool_response=self.agent.process_use_tool(response.tool_name)
            response_history.append({"role": "assistant", "content": tool_response})
            tool=tool_response["tool_name"]
            call_tool=self.agent.process_use_tool(tool)
            response_history.append({"role": "process_tool_call", "content": call_tool})
            result=await self.session.call_tool(tool,call_tool["input"]) 
            response_history.append({"role": "tool_call_result", "content": result})
            final_response=self.agent.generate_response(f"""
            You are a final response generator.
            You are giving a conversation history between a chatbot and a user and inside this conversation history lies processes like tool calls and results of tool calls.
            You are to use the result of the tool call to generate a final response for the user.
            You are to only generate the final response for the user.
            You are to not generate any other text.
            You are to not generate any tool calls.
            The conversation history is as follows:
            {response_history}
            """)
            return final_response
        else:
            response=self.agent.generate_response(input)
            response_history.append({"role": "assistant", "content": response})
            return response 

        

            
    async def chat_loop(self):
        """Main chat loop for interacting with the MCP server"""
        print("Chat session started. Type 'exit' to quit.")
        
        while True:
            try:
                # Get user input
                user_input = input("\nYou: ").strip()
                
                # Check for exit command
                if user_input.lower() == 'exit':
                    print("Ending chat session...")
                    break
                
                # Skip empty inputs
                if not user_input:
                    continue
                
                # Process the input and get response
                response = await self.get_response(user_input)
                
                # Print the response
                if response:
                    print("\nAssistant:", response)
                    
            except Exception as e:
                print(f"\nError occurred: {str(e)}")
                continue
