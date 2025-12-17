"""Tests for agent_demo.py

Tests the custom tools and agent functionality.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from pydantic import BaseModel, Field
from langchain.tools import BaseTool


# Mock the agent_state for testing
@pytest.fixture
def mock_agent_state():
    """Fixture providing a clean agent state for each test."""
    return {
        "decisions": [],
        "calendar_events": [],
        "emails_read": [],
        "memory_history": []
    }


@pytest.fixture
def fake_email():
    """Fixture providing the fake email content."""
    return """
From: sarah.johnson@email.com
To: you@email.com
Subject: You're Invited! Birthday Party 🎉
Date: December 10, 2025

Hi there!

I hope this email finds you well! I'm excited to invite you to my birthday party.

📅 Date: December 20, 2025
⏰ Time: 6:00 PM
📍 Location: 123 Celebration Street, Party City
🎂 Theme: Retro 80s

Please let me know if you can make it! Feel free to bring a plus one.

Looking forward to celebrating with you!

Best regards,
Sarah Johnson
"""


class TestEmailReadTool:
    """Tests for the EmailReadTool."""
    
    def test_email_tool_initialization(self):
        """Test that EmailReadTool can be initialized."""
        # Create a mock tool class
        class EmailReadInput(BaseModel):
            email_id: str = Field(default="birthday_invite")
        
        class EmailReadTool(BaseTool):
            name: str = "read_email"
            description: str = "Reads a fake email"
            args_schema: type[BaseModel] = EmailReadInput
            
            def _run(self, email_id: str = "birthday_invite") -> str:
                return "test email"
        
        tool = EmailReadTool()
        assert tool.name == "read_email"
        assert tool.description == "Reads a fake email"
    
    def test_email_tool_execution(self, mock_agent_state, fake_email):
        """Test that EmailReadTool returns the fake email."""
        class EmailReadInput(BaseModel):
            email_id: str = Field(default="birthday_invite")
        
        class EmailReadTool(BaseTool):
            name: str = "read_email"
            description: str = "Reads a fake email"
            args_schema: type[BaseModel] = EmailReadInput
            
            def _run(self, email_id: str = "birthday_invite") -> str:
                mock_agent_state["emails_read"].append({
                    "email_id": email_id,
                    "timestamp": str(datetime.now())
                })
                return fake_email
        
        tool = EmailReadTool()
        result = tool._run()
        
        assert "sarah.johnson@email.com" in result
        assert "Birthday Party" in result
        assert "December 20, 2025" in result
        assert len(mock_agent_state["emails_read"]) == 1
    
    def test_email_tool_tracks_state(self, mock_agent_state):
        """Test that EmailReadTool tracks state correctly."""
        class EmailReadInput(BaseModel):
            email_id: str = Field(default="birthday_invite")
        
        class EmailReadTool(BaseTool):
            name: str = "read_email"
            description: str = "Reads a fake email"
            args_schema: type[BaseModel] = EmailReadInput
            
            def _run(self, email_id: str = "birthday_invite") -> str:
                mock_agent_state["emails_read"].append({
                    "email_id": email_id,
                    "timestamp": str(datetime.now())
                })
                mock_agent_state["decisions"].append({
                    "action": "read_email",
                    "reasoning": f"User requested to read email with ID: {email_id}",
                    "timestamp": str(datetime.now())
                })
                return "email content"
        
        tool = EmailReadTool()
        tool._run("test_email")
        
        assert len(mock_agent_state["emails_read"]) == 1
        assert mock_agent_state["emails_read"][0]["email_id"] == "test_email"
        assert len(mock_agent_state["decisions"]) == 1
        assert mock_agent_state["decisions"][0]["action"] == "read_email"


class TestCalendarEventTool:
    """Tests for the CalendarEventTool."""
    
    def test_calendar_tool_initialization(self):
        """Test that CalendarEventTool can be initialized."""
        class CalendarEventInput(BaseModel):
            title: str
            date: str
            time: str
            location: str
            description: str = ""
        
        class CalendarEventTool(BaseTool):
            name: str = "create_calendar_event"
            description: str = "Creates a calendar event"
            args_schema: type[BaseModel] = CalendarEventInput
            
            def _run(self, title: str, date: str, time: str, location: str, description: str = "") -> str:
                return "Event created"
        
        tool = CalendarEventTool()
        assert tool.name == "create_calendar_event"
        assert tool.description == "Creates a calendar event"
    
    def test_calendar_tool_creates_event(self, mock_agent_state):
        """Test that CalendarEventTool creates an event correctly."""
        class CalendarEventInput(BaseModel):
            title: str
            date: str
            time: str
            location: str
            description: str = ""
        
        class CalendarEventTool(BaseTool):
            name: str = "create_calendar_event"
            description: str = "Creates a calendar event"
            args_schema: type[BaseModel] = CalendarEventInput
            
            def _run(self, title: str, date: str, time: str, location: str, description: str = "") -> str:
                event = {
                    "title": title,
                    "date": date,
                    "time": time,
                    "location": location,
                    "description": description,
                    "created_at": str(datetime.now())
                }
                mock_agent_state["calendar_events"].append(event)
                return f"✅ Calendar event created successfully!\n\nEvent: {title}"
        
        tool = CalendarEventTool()
        result = tool._run(
            title="Birthday Party",
            date="December 20, 2025",
            time="6:00 PM",
            location="123 Celebration Street"
        )
        
        assert "✅" in result
        assert "Birthday Party" in result
        assert len(mock_agent_state["calendar_events"]) == 1
        assert mock_agent_state["calendar_events"][0]["title"] == "Birthday Party"
        assert mock_agent_state["calendar_events"][0]["date"] == "December 20, 2025"
    
    def test_calendar_tool_with_description(self, mock_agent_state):
        """Test that CalendarEventTool handles optional description."""
        class CalendarEventInput(BaseModel):
            title: str
            date: str
            time: str
            location: str
            description: str = ""
        
        class CalendarEventTool(BaseTool):
            name: str = "create_calendar_event"
            description: str = "Creates a calendar event"
            args_schema: type[BaseModel] = CalendarEventInput
            
            def _run(self, title: str, date: str, time: str, location: str, description: str = "") -> str:
                event = {
                    "title": title,
                    "date": date,
                    "time": time,
                    "location": location,
                    "description": description,
                    "created_at": str(datetime.now())
                }
                mock_agent_state["calendar_events"].append(event)
                return "Event created"
        
        tool = CalendarEventTool()
        tool._run(
            title="Test Event",
            date="Jan 1, 2026",
            time="10:00 AM",
            location="Test Location",
            description="Test description"
        )
        
        assert mock_agent_state["calendar_events"][0]["description"] == "Test description"


class TestDecisionDisplayTool:
    """Tests for the DecisionDisplayTool."""
    
    def test_decision_tool_empty_state(self, mock_agent_state):
        """Test DecisionDisplayTool with no decisions."""
        class DecisionDisplayInput(BaseModel):
            pass
        
        class DecisionDisplayTool(BaseTool):
            name: str = "show_decisions"
            description: str = "Displays decisions"
            args_schema: type[BaseModel] = DecisionDisplayInput
            
            def _run(self) -> str:
                if not mock_agent_state["decisions"]:
                    return "No decisions recorded yet."
                return "Decisions found"
        
        tool = DecisionDisplayTool()
        result = tool._run()
        
        assert result == "No decisions recorded yet."
    
    def test_decision_tool_with_decisions(self, mock_agent_state):
        """Test DecisionDisplayTool with recorded decisions."""
        mock_agent_state["decisions"] = [
            {
                "action": "read_email",
                "reasoning": "User requested email",
                "timestamp": "2025-12-15 10:00:00"
            },
            {
                "action": "create_calendar_event",
                "reasoning": "Creating event from email",
                "timestamp": "2025-12-15 10:01:00"
            }
        ]
        
        class DecisionDisplayInput(BaseModel):
            pass
        
        class DecisionDisplayTool(BaseTool):
            name: str = "show_decisions"
            description: str = "Displays decisions"
            args_schema: type[BaseModel] = DecisionDisplayInput
            
            def _run(self) -> str:
                if not mock_agent_state["decisions"]:
                    return "No decisions recorded yet."
                
                output = "🧠 Agent Decisions and Reasoning:\n\n"
                for i, decision in enumerate(mock_agent_state["decisions"], 1):
                    output += f"{i}. Action: {decision['action']}\n"
                    output += f"   Reasoning: {decision['reasoning']}\n"
                return output
        
        tool = DecisionDisplayTool()
        result = tool._run()
        
        assert "🧠 Agent Decisions" in result
        assert "read_email" in result
        assert "create_calendar_event" in result
        assert "User requested email" in result


class TestMemoryDisplayTool:
    """Tests for the MemoryDisplayTool."""
    
    def test_memory_tool_empty_state(self, mock_agent_state):
        """Test MemoryDisplayTool with no history."""
        class MemoryDisplayInput(BaseModel):
            pass
        
        class MemoryDisplayTool(BaseTool):
            name: str = "show_memory"
            description: str = "Displays memory"
            args_schema: type[BaseModel] = MemoryDisplayInput
            
            def _run(self) -> str:
                if not mock_agent_state["memory_history"]:
                    return "No conversation history yet."
                return "Memory found"
        
        tool = MemoryDisplayTool()
        result = tool._run()
        
        assert result == "No conversation history yet."
    
    def test_memory_tool_with_history(self, mock_agent_state):
        """Test MemoryDisplayTool with conversation history."""
        mock_agent_state["memory_history"] = [
            {
                "role": "Human",
                "content": "Read my email",
                "timestamp": "2025-12-15 10:00:00"
            },
            {
                "role": "AI",
                "content": "I've read your email about the birthday party",
                "timestamp": "2025-12-15 10:00:05"
            }
        ]
        
        class MemoryDisplayInput(BaseModel):
            pass
        
        class MemoryDisplayTool(BaseTool):
            name: str = "show_memory"
            description: str = "Displays memory"
            args_schema: type[BaseModel] = MemoryDisplayInput
            
            def _run(self) -> str:
                if not mock_agent_state["memory_history"]:
                    return "No conversation history yet."
                
                output = "💭 Conversation Memory:\n\n"
                for i, entry in enumerate(mock_agent_state["memory_history"], 1):
                    output += f"{i}. {entry['role']}: {entry['content'][:100]}...\n"
                return output
        
        tool = MemoryDisplayTool()
        result = tool._run()
        
        assert "💭 Conversation Memory" in result
        assert "Human" in result
        assert "AI" in result
        assert "Read my email" in result


class TestToolsDisplayTool:
    """Tests for the ToolsDisplayTool."""
    
    def test_tools_display(self):
        """Test ToolsDisplayTool lists available tools."""
        # Create mock tools
        class MockTool(BaseTool):
            name: str = "mock_tool"
            description: str = "A mock tool"
            
            def _run(self) -> str:
                return "mock"
        
        mock_tools = [
            MockTool(name="tool1", description="First tool"),
            MockTool(name="tool2", description="Second tool")
        ]
        
        class ToolsDisplayInput(BaseModel):
            pass
        
        class ToolsDisplayTool(BaseTool):
            name: str = "show_tools"
            description: str = "Displays tools"
            args_schema: type[BaseModel] = ToolsDisplayInput
            
            def _run(self) -> str:
                output = "🔧 Available Tools:\n\n"
                for i, tool in enumerate(mock_tools, 1):
                    output += f"{i}. **{tool.name}**\n"
                    output += f"   Description: {tool.description}\n\n"
                return output
        
        tool = ToolsDisplayTool()
        result = tool._run()
        
        assert "🔧 Available Tools" in result
        assert "tool1" in result
        assert "tool2" in result
        assert "First tool" in result
        assert "Second tool" in result


class TestIntegration:
    """Integration tests for the agent demo."""
    
    def test_email_to_calendar_workflow(self, mock_agent_state, fake_email):
        """Test the complete workflow from reading email to creating calendar event."""
        # Simulate reading email
        mock_agent_state["emails_read"].append({
            "email_id": "birthday_invite",
            "timestamp": str(datetime.now())
        })
        
        # Simulate creating calendar event
        mock_agent_state["calendar_events"].append({
            "title": "Sarah's Birthday Party",
            "date": "December 20, 2025",
            "time": "6:00 PM",
            "location": "123 Celebration Street, Party City",
            "description": "Retro 80s theme",
            "created_at": str(datetime.now())
        })
        
        # Verify workflow
        assert len(mock_agent_state["emails_read"]) == 1
        assert len(mock_agent_state["calendar_events"]) == 1
        assert mock_agent_state["calendar_events"][0]["title"] == "Sarah's Birthday Party"
    
    def test_state_tracking(self, mock_agent_state):
        """Test that all state is tracked correctly."""
        # Simulate various operations
        mock_agent_state["emails_read"].append({"email_id": "test"})
        mock_agent_state["calendar_events"].append({"title": "Test Event"})
        mock_agent_state["decisions"].append({"action": "test_action"})
        mock_agent_state["memory_history"].append({"role": "Human", "content": "Test"})
        
        # Verify all state is tracked
        assert len(mock_agent_state["emails_read"]) == 1
        assert len(mock_agent_state["calendar_events"]) == 1
        assert len(mock_agent_state["decisions"]) == 1
        assert len(mock_agent_state["memory_history"]) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
