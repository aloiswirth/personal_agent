"""Base agent class for all domain agents."""

from abc import ABC, abstractmethod
from typing import Any, Optional

from langchain_core.tools import BaseTool
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import InMemorySaver

from src.config import get_settings


class BaseAgent(ABC):
    """Abstract base class for domain agents.
    
    All domain agents (Communication, Finance, Media) should inherit from this class.
    """

    def __init__(
        self,
        name: str,
        description: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
    ):
        """Initialize base agent.
        
        Args:
            name: Agent name (e.g., "communication", "finance")
            description: Agent description for the orchestrator
            model: LLM model to use (defaults to settings)
            temperature: LLM temperature
        """
        self.name = name
        self.description = description
        self.settings = get_settings()
        
        self.llm = ChatOpenAI(
            model=model or self.settings.openai_model,
            temperature=temperature,
            api_key=self.settings.openai_api_key,
        )
        
        self.checkpointer = InMemorySaver()
        self._agent = None
        self._state: dict[str, Any] = {
            "decisions": [],
            "errors": [],
        }

    @property
    @abstractmethod
    def tools(self) -> list[BaseTool]:
        """Return list of tools available to this agent.
        
        Subclasses must implement this to provide domain-specific tools.
        """
        pass

    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """Return the system prompt for this agent.
        
        Subclasses must implement this to provide domain-specific instructions.
        """
        pass

    def create_agent(self):
        """Create the LangGraph agent with tools and memory."""
        if self._agent is None:
            self._agent = create_react_agent(
                model=self.llm,
                tools=self.tools,
                prompt=self.system_prompt,
                checkpointer=self.checkpointer,
            )
        return self._agent

    def invoke(self, message: str, thread_id: str = "default") -> str:
        """Invoke the agent with a message.
        
        Args:
            message: User message to process
            thread_id: Conversation thread ID for memory
            
        Returns:
            Agent response as string
        """
        agent = self.create_agent()
        config = {"configurable": {"thread_id": thread_id}}
        
        result = agent.invoke(
            {"messages": [{"role": "user", "content": message}]},
            config
        )
        
        # Get the last AI message
        last_message = result["messages"][-1]
        return last_message.content

    async def ainvoke(self, message: str, thread_id: str = "default") -> str:
        """Async invoke the agent with a message."""
        agent = self.create_agent()
        config = {"configurable": {"thread_id": thread_id}}
        
        result = await agent.ainvoke(
            {"messages": [{"role": "user", "content": message}]},
            config
        )
        
        last_message = result["messages"][-1]
        return last_message.content

    def log_decision(self, action: str, reasoning: str) -> None:
        """Log a decision made by the agent."""
        from datetime import datetime
        self._state["decisions"].append({
            "action": action,
            "reasoning": reasoning,
            "timestamp": datetime.now().isoformat(),
        })

    def log_error(self, error: str, context: str = "") -> None:
        """Log an error encountered by the agent."""
        from datetime import datetime
        self._state["errors"].append({
            "error": error,
            "context": context,
            "timestamp": datetime.now().isoformat(),
        })

    def get_state(self) -> dict[str, Any]:
        """Get the current agent state."""
        return self._state.copy()

    def reset_state(self) -> None:
        """Reset the agent state."""
        self._state = {
            "decisions": [],
            "errors": [],
        }
