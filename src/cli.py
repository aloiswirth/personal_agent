"""CLI entry point for the Personal Agent."""

import sys
from src.agents.communication import CommunicationAgent


def main():
    """Main CLI entry point."""
    print("🤖 Personal Agent - Communication Module")
    print("=" * 50)
    print("\nCapabilities:")
    print("- 📧 Email reading")
    print("- 📅 Calendar management")
    print("\nType 'quit' or 'exit' to stop.")
    print("=" * 50)

    agent = CommunicationAgent()
    thread_id = "cli-session"

    while True:
        try:
            user_input = input("\n👤 You: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Goodbye!")
                break

            print("\n🤖 Agent: ", end="", flush=True)
            response = agent.invoke(user_input, thread_id=thread_id)
            print(response)

        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")


if __name__ == "__main__":
    main()
