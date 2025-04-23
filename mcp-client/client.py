import asyncio
import sys
import os
import json
from typing import Optional
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessageParam
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from contextlib import AsyncExitStack
from dotenv import load_dotenv

load_dotenv()

class MCPClient:
    def __init__(self):
        # Initialize session and client objects
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.openai_client = AsyncOpenAI()  # Uses OPENAI_API_KEY from env by default

    async def connect_to_server(self, server_script_path: str):
        """Connect to an MCP server"""
        is_python = server_script_path.endswith('.py')
        is_js = server_script_path.endswith('.js')
        if not (is_python or is_js):
            raise ValueError("Server script must be a .py or .js file")

        command = "python" if is_python else "node"
        server_params = StdioServerParameters(command=command, args=[server_script_path], env=None)

        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
        self.stdio, self.write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))

        await self.session.initialize()

        response = await self.session.list_tools()
        tools = response.tools
        print("\nConnected to server with tools:", [tool.name for tool in tools])

    async def process_query(self, query: str) -> str:
        """Process a query using ChatGPT and available tools"""
        print("Processing a query using ChatGPT and available tools")
        messages: list[ChatCompletionMessageParam] = [
            {"role": "user", "content": query}
        ]

        response = await self.session.list_tools()
        available_tools = [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.inputSchema
                }
            }
            for tool in response.tools
        ]

        final_text = []

        while True:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4-turbo",
                messages=messages,
                tools=available_tools,
                tool_choice="auto",
                max_tokens=1000
            )

            reply = response.choices[0].message
            messages.append(reply)

            if reply.tool_calls:
                for tool_call in reply.tool_calls:
                    tool_name = tool_call.function.name
                    print("Using tool: " + tool_name)
                    tool_args = json.loads(tool_call.function.arguments)

                    result = await self.session.call_tool(tool_name, tool_args)
                    final_text.append(f"[Calling tool {tool_name} with args {tool_args}]")

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result.content
                    })
            else:
                final_text.append(reply.content or "")
                break

        return "\n".join(final_text)

    async def chat_loop(self):
        """Run an interactive chat loop"""
        print("\nMCP Client Started!")
        print("Summarizing message for selected Channel...")
        channel_name = ""
        if channel_name == "":
            print("Channel name to summarize needed. Kindly add.")
            sys.exit(1)
        try:
            query = """Summarize today's Slack activity in %s with the following details:

                    1. **Total Message Count:** Provide the total number of messages sent across all channels and direct messages today.

                    2. **Dominant Tone:** Identify the most prevalent tone expressed in the messages. Options could include (but are not limited to): positive, negative, neutral, inquisitive, urgent, humorous, or collaborative. Briefly explain why you identified this as the dominant tone, perhaps by mentioning recurring sentiment or types of language used.

                    3. **Topic Summary by Time Grouping:** Summarize the main topics discussed throughout the day. Group these summaries chronologically. For each time block where a distinct topic or set of related topics emerged, provide a concise summary of the discussion. For example, if there was a discussion about "project alpha" around 9:00 AM and then a separate discussion about "marketing campaign updates" around 11:00 AM, these should be summarized separately under their approximate timeframes. Be sure to capture the essence of each conversation without going into excessive detail.
                    """ % channel_name

            response = await self.process_query(query)
            print("\n\033[94m" + response + "\033[0m") #You can either print this or send it to WhatsApp, Email or your preferred channel
            return 0;
        except Exception as e:
            print(f"\nError: {str(e)}")
            return 1;

    async def cleanup(self):
        """Clean up resources"""
        await self.exit_stack.aclose()


async def run_once():
    client = MCPClient()
    try:
        mcp_server_path = ""
        if mcp_server_path == "":
            print("MCP server path needed. Kindly add.")
            sys.exit(1)
        await client.connect_to_server(mcp_server_path)
        await client.chat_loop()
        return 0;
    finally:
        await client.cleanup()
async def main(n_minutes):
    print("Running immediately...")
    await run_once()

    while True:
        print(f"\nWaiting {n_minutes} minute(s) before next run...\n")
        await asyncio.sleep(n_minutes * 60)

        print("Running again after delay...")
        await run_once()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python client.py <delay_in_minutes>")
        sys.exit(1)

    try:
        delay_minutes = float(sys.argv[1])
    except ValueError:
        print("Delay must be a number (integer or float).")
        sys.exit(1)

    asyncio.run(main(delay_minutes))
