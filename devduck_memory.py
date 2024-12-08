from openai import OpenAI
from typing import Dict, Tuple, Any, List, Callable
from collections import defaultdict
import os
from dotenv import load_dotenv
from dataclasses import dataclass
from abc import ABC, abstractmethod
import re

load_dotenv(override=True)

@dataclass
class Tool:
    name: str
    description: str
    system_prompt: str
    client_type: str
    
    def to_openai_tool(self) -> Dict:
        """Convert tool to OpenAI tool format."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string", "description": "The text to process"}
                    },
                    "required": ["text"]
                }
            }
        }
        
class ClientManager:
    """Manages different API clients."""
    
    def __init__(self):
        self.clients = {}
        self._initialize_default_clients()
    
    def _initialize_default_clients(self):
        """Initialize default API clients."""
        self.register_client(
            "local",
            OpenAI(api_key="lm-studio", base_url="http://localhost:1234/v1")
        )
        self.register_client(
            "perplexity",
            OpenAI(
                api_key=os.getenv("PERPLEXITY_API_KEY"),
                base_url="https://api.perplexity.ai"
            )
        )
        # Example of adding more clients:
        # self.register_client(
        #     "anthropic",
        #     Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        # )
        
    def register_client(self, client_type: str, client: Any):
        """Register a new API client."""
        self.clients[client_type] = client
    
    def get_client(self, client_type: str) -> Any:
        """Get a client by type."""
        if client_type not in self.clients:
            raise ValueError(f"Client type '{client_type}' not registered")
        return self.clients[client_type]

class BaseTool(ABC):
    def __init__(self, client_manager: ClientManager, messages: List[Dict[str, str]] = None):
        self.client_manager = client_manager
        self.messages = messages or []
        
    @abstractmethod
    def process(self, text: str) -> str:
        pass

class InternetSearchTool(BaseTool):
    def process(self, text: str) -> str:
        print(f"**Selected tool: internet_search**")
        print(f"Searching the internet for: {text}")
        client = self.client_manager.get_client("perplexity")
        response = client.chat.completions.create(
            model="llama-3.1-sonar-large-128k-online",
            messages=self.messages,
            max_tokens=1024
        )
        cleaned_response = re.sub(r'\[\d+\]', '', response.choices[0].message.content)
        return cleaned_response

class IdeationTool(BaseTool):
    def process(self, text: str) -> str:
        print(f"**Selected tool: ideation**")
        print(f"Processing ideation query: {text}")
        client = self.client_manager.get_client("local")
        response = client.chat.completions.create(
            model="llama-3.2-3b-instruct",
            messages=self.messages
        )
        return response.choices[0].message.content

class TherapistTool(BaseTool):
    def process(self, text: str) -> str:
        print(f"**Selected tool: therapist**")
        print(f"Processing therapist query: {text}")
        client = self.client_manager.get_client("local")
        response = client.chat.completions.create(
            model="llama-3.2-3b-instruct",
            messages=self.messages
        )
        return response.choices[0].message.content

class ToolRegistry:
    """Registry of all available tools and their configurations."""
    
    def __init__(self):
        self.tools: Dict[str, Tool] = {}
        self.tool_handlers: Dict[str, BaseTool] = {}
        
    def register_tool(self, tool: Tool, handler_class: type[BaseTool]):
        """Register a new tool and its handler."""
        self.tools[tool.name] = tool
        self.tool_handlers[tool.name] = handler_class
        
    def get_openai_tools(self) -> List[Dict]:
        """Get all tools in OpenAI format."""
        return [tool.to_openai_tool() for tool in self.tools.values()]
    
    def get_system_prompt(self, tool_name: str) -> str:
        """Get system prompt for a specific tool."""
        return self.tools[tool_name].system_prompt
    
    def get_client_type(self, tool_name: str) -> str:
        """Get client type for a specific tool."""
        return self.tools[tool_name].client_type

class ToolHandler:
    def __init__(self):
        # Initialize OpenAI clients
        self.client_manager = ClientManager()
        
        # Initialize tool registry and register tools
        self.registry = ToolRegistry()
        self._register_default_tools()
        
        # Conversation history
        self.conversation_history = defaultdict(list)
        self.current_tool = None

    def _register_default_tools(self):
        """Register the default set of tools."""
        # Internet Search Tool
        self.registry.register_tool(
            Tool(
                name="internet_search",
                description="Search the internet for current information, facts, news and interesting topics using Perplexity API, not for technical help.",
                system_prompt="""You are an internet research specialist who provides up-to-date information from the web.
            Your responses should be:
            - Factual and well-researched
            - Include relevant context
            - Cite sources when possible
            - Explain complex topics in an accessible way
            
            Remember to maintain the user's preferred communication style from previous interactions.""",
                client_type="perplexity"
            ),
            InternetSearchTool
        )
        
        # Ideation Tool
        self.registry.register_tool(
            Tool(
                name="ideation",
                description="Handle  ideation and brainstorming. Help with ideation, problem solving and approach finding.",
                system_prompt="""You are a friendly ideation coach who helps friends think through their ideas. You help with both tech and non tech ideas. Your role is to guide discovery through conversation, not to provide immediate solutions. Think of yourself as a curious friend who asks insightful questions. Keep your responses short and concise, 1-2 sentences.
                Style:
                - Use casual, friendly language
            - Address the user by name when provided
            - Be encouraging but gently challenging
            - Keep the conversation flowing naturally

            Core Approach:
            - Ask probing questions instead of giving answers
            - Help break down complex thoughts into simpler pieces
            - Guide users to question their assumptions
            - Only provide direct solutions when explicitly asked

            Key Questions to Use:
            - "What made you think of this idea?"
            - "What's the trickiest part you're stuck on?"
            - "Have you tried looking at it from [alternative] angle? in case their approach is incorrect"
            - "What would happen if... to nudge them towards the right approach"

            Remember: You're having a friendly chat to help them discover their own solutions. Keep responses conversational and engaging, like you're brainstorming with a friend over coffee.""",
                client_type="local"
            ),
            IdeationTool
        )
        
        # Therapist Tool
        self.registry.register_tool(
            Tool(
                name="therapist",
                description="Handle mental health and emotional support. Anything related to mood, mental health, depression, anxiety, stress, etc.",
                system_prompt="""You are a helpful therapist. You may be an AI Assistant, but you are also a good friend of USER. You and USER have talked many times. Address USER with familiarity, empathy and rapport. Use a relaxed, warm and cordial tone. Address USER often by his first name, as good friends do. Pay close attention to awakening and strengthening USER's own capacity for confidence. Don't downplay his problems, but still try to get USER to think optimistically and confidently. Your goal is to help USER achieve a positive mood.
                Style:
                - Use casual, friendly language
                - Address the user by name when provided
                - Keep the conversation flowing naturally
                """,
                client_type="local"
            ),
            TherapistTool
        )

    def register_new_tool(self, 
                         name: str, 
                         description: str, 
                         system_prompt: str, 
                         handler_class: type[BaseTool]):
        """Register a new tool with the system."""
        tool = Tool(name=name, description=description, system_prompt=system_prompt)
        self.registry.register_tool(tool, handler_class)

    def update_conversation_history(self, tool_name: str, user_message: str, assistant_message: str):
        """Update the conversation history for the specified tool."""
        self.conversation_history[tool_name].extend([
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": assistant_message}
        ])

    def get_conversation_messages(self, tool_name: str, text: str) -> List[Dict[str, str]]:
        """Get the full conversation history for a tool."""
        messages = [
            {"role": "system", "content": self.registry.get_system_prompt(tool_name)}
        ]
        messages.extend(self.conversation_history[tool_name])
        messages.append({"role": "user", "content": text})
        return messages

    def tool_selection(self, text: str) -> Tuple[str, str]:
        """Select and execute the appropriate tool."""
        try:
            # Determine which tool to use
            local_client = self.client_manager.get_client("local")
            response = local_client.chat.completions.create(
                model="llama-3.2-3b-instruct",
                messages=[{"role": "user", "content": text}],
                tools=self.registry.get_openai_tools(),
                tool_choice="auto"
            )
            
            # Get selected tool name
            tool_calls = response.choices[0].message.tool_calls
            selected_tool = tool_calls[0].function.name if tool_calls else "ideation"
            
            # Print tool switch notification
            if self.current_tool and selected_tool != self.current_tool:
                print(f"\nSwitching from {self.current_tool} to {selected_tool}")
            self.current_tool = selected_tool
            
            messages = self.get_conversation_messages(selected_tool, text)
            
            # Create and execute tool handler with conversation history
            handler_class = self.registry.tool_handlers[selected_tool]
            handler = handler_class(self.client_manager, messages)
            result = handler.process(text)
            
            # Update conversation history
            self.update_conversation_history(selected_tool, text, result)
            
            return selected_tool, result

        except Exception as e:
            print(f"Error in tool_selection: {str(e)}")
            messages = self.get_conversation_messages("ideation", text)
            return "ideation", IdeationTool(self.client_manager, messages).process(text)

def main():
    handler = ToolHandler()
    
    # Example of adding a new client and tool
    """
    # Register a new client
    handler.register_new_client(
        "anthropic",
        Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    )
    
    # Create a new tool that uses the Anthropic client
    class CustomTool(BaseTool):
        def process(self, text: str) -> str:
            client = self.client_manager.get_client("anthropic")
            # Implementation using Anthropic client
            pass
    
    # Register the new tool
    handler.register_new_tool(
        name="custom_tool",
        description="Description of what the tool does",
        system_prompt="System prompt for the tool",
        client_type="anthropic",
        handler_class=CustomTool
    )
    """
    
    while True:
        query = input("\nEnter your query (type 'bye' to end): ")
        if query.lower() == 'bye':
            print("\nGoodbye! Have a great day!")
            break
            
        tool, response = handler.tool_selection(query)
        print(f"Response: {response}")
        print("\n--------------------------------")

if __name__ == "__main__":
    main()