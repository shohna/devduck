from openai import OpenAI
from typing import Dict, Tuple, Any, List, Callable
from collections import defaultdict
import os
from dataclasses import dataclass
from abc import ABC, abstractmethod
import re

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
    def __init__(self, client_manager: ClientManager):
        self.client_manager = client_manager
        
    @abstractmethod
    def process(self, text: str, history:str) -> str:
        pass

class InternetSearchTool(BaseTool):
    def process(self, text: str, history:str) -> str:
        print(f"**Selected tool: internet_search**")
        print(f"Searching the internet for: {text}")
        client = self.client_manager.get_client("perplexity")
        response = client.chat.completions.create(
            model="llama-3.1-sonar-large-128k-online",
            messages=[{"role": "user", "content": text + f"Here is the conversation history: {history}"}],
            max_tokens=1024,
            stream=True
        )
        for chunk in response:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content


class IdeationTool(BaseTool):
    def process(self, text: str, history:str) -> str:
        print(f"**Selected tool: ideation**")
        print(f"Processing ideation query: {text}")
        print(f"history: {history}")
        client = self.client_manager.get_client("local")
        input_text = f"You are an ideation specialist. Do not immediately provide solutions. Always ask questions to help the user think through their ideas: {text}"
        response = client.chat.completions.create(
            model="llama-3.2-3b-qnn",
            messages= history + [{"role": "user", "content": input_text}],
            stream=True
        )
        for chunk in response:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

class TherapistTool(BaseTool):
    def process(self, text: str, history:str) -> str:
        print(f"**Selected tool: therapist**")
        print(f"Processing therapist query: {text}")
        print(f"history: {history}")
        client = self.client_manager.get_client("local")
        input_text = f"Talk to the user about their mental health and provide emotional support: {text}. Here is the conversation history: {history}"
        response = client.chat.completions.create(
            model="llama-3.2-3b-qnn",
            messages= history + [{"role": "user", "content": input_text}],
            stream=True
        )
        for chunk in response:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
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
        self.conversation_history = defaultdict(lambda: defaultdict(list))
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
                - Limit the response to 400 words.
                
                Remember to maintain the user's preferred communication style from previous interactions.""",
                client_type="perplexity"
            ),
            InternetSearchTool
        )
        
        # Ideation Tool
        self.registry.register_tool(
            Tool(
                name="ideation",
                description="Handle ideation and brainstorming. Help with ideation, problem solving and approach finding.",
                system_prompt="""
                You are a friendly ideation coach helping people explore and develop their ideas. Your role is to guide discovery through conversation, not to provide immediate solutions. Think of yourself as a curious friend who asks insightful questions. Keep your responses short and concise, typically 1-2 sentences.
                Style:
                - Use casual, friendly language
                - Address the user by name if provided
                - Be encouraging but gently challenging
                - Keep the conversation flowing naturally
                - Keep your responses short and concise, typically 1-2 sentences.

                Core Approach:
                - Ask probing questions to deepen understanding
                - Help break down complex thoughts into simpler components
                - Guide users to question their assumptions
                - Only provide direct solutions when explicitly asked

                Key Questions to Consider:
                - "What inspired this idea?"
                - "What's the most challenging aspect you're facing?"
                - "Have you considered looking at it from [alternative] perspective?"
                - "What would happen if you [suggest a twist or variation]?"
                - "How might you approach this differently?"

                Context Awareness:
                - Carefully review the conversation history before responding
                - Avoid asking questions that have already been answered
                - Build upon previous responses to maintain continuity
                - If clarification is needed, phrase it as "Earlier you mentioned X. Can you elaborate on how that relates to Y?"

                Remember: You're having a friendly chat to help them discover their own solutions. Keep responses conversational and engaging, as if you're brainstorming with a friend over coffee. Adapt your questions and approach based on the specific idea or topic presented, while maintaining context from the entire conversation.
                """,
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
                - Limit the response to 400 words.
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

    def update_conversation_history(self, tool_name: str, user_message: str, assistant_message: str, session_id):
        """Update the conversation history for the specified tool."""
        self.conversation_history[session_id][tool_name].extend([
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": assistant_message}
        ])

    def get_conversation_messages(self, tool_name: str, text: str, session_id) -> List[Dict[str, str]]:
        """Get the full conversation history for a tool."""
        messages = self.conversation_history[session_id][tool_name]
        return messages

    def tool_selection(self, text: str, session_id) -> Tuple[str, str]:
        """Select and execute the appropriate tool."""
        try:
            # Determine which tool to use
            local_client = self.client_manager.get_client("local")
            tool_selection_prompt = f"You are an expert decision maker. I want your help to make a tool choice depending on the tools provided. Tools: {self.registry.get_openai_tools()}. Here is the text that you should use to decide what tool to use: {text}. Return only the tool name. Previously used tool: {self.current_tool}. It might be a follow up question."
            response = local_client.chat.completions.create(
                model="llama-3.2-3b-instruct",
                messages=[{"role": "user", "content": tool_selection_prompt}],
                tools=self.registry.get_openai_tools(),
                tool_choice="auto"
            )
            
            # Get selected tool name
            tool_calls = response.choices[0].message.content
            selected_tool = tool_calls if tool_calls else "ideation"
            
            # Print tool switch notification
            if self.current_tool and selected_tool != self.current_tool:
                print(f"\nSwitching from {self.current_tool} to {selected_tool}")
            self.current_tool = selected_tool
            
            messages = self.get_conversation_messages(selected_tool, text, session_id)
            print(f"Messages ss : {messages}")
            if not messages:
                messages = [{"role": "system", "content": self.registry.get_system_prompt(selected_tool)}]
                
            # Create and execute tool handler
            handler_class = self.registry.tool_handlers[selected_tool]
            handler = handler_class(self.client_manager)
            result = handler.process(text, messages)
            
            return selected_tool, result

        except Exception as e:
            print(f"Error in tool_selection: {str(e)}")
            messages = self.get_conversation_messages("ideation", text, session_id)
            return "ideation", IdeationTool(self.client_manager).process(text, messages)

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
        print(f"Response:")
        for i in response:
            print(i, end="")
        
        print("\n--------------------------------")

if __name__ == "__main__":
    main()