#!/usr/bin/env python3
"""
Quick Demo Script for Gliksbot CLI

This script demonstrates the key features of the CLI interface.
Run this after setting up the CLI to see how it works.
"""

import os
import subprocess
import sys

def print_header(title):
    """Print a formatted header."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def print_step(step_num, description):
    """Print a formatted step."""
    print(f"\n{step_num}. {description}")

def main():
    """Run the CLI demo."""
    print_header("Gliksbot CLI - Quick Demo")
    
    print("\n🤖 Welcome to the Gliksbot CLI-based Local UI!")
    print("This interface provides 5 LLM panels for local multi-LLM collaboration.")
    
    print_step(1, "Prerequisites Check")
    
    # Check if required packages are installed
    try:
        import textual
        print("✓ Textual library is available")
    except ImportError:
        print("✗ Textual library not found. Install with: pip install textual")
        return 1
    
    try:
        import httpx
        print("✓ HTTPX library is available")
    except ImportError:
        print("✗ HTTPX library not found. Install with: pip install httpx")
        return 1
    
    # Check if config exists
    if os.path.exists("config.json"):
        print("✓ Configuration file found")
    else:
        print("⚠ No config.json found - will create default configuration")
    
    print_step(2, "CLI Interface Features")
    print("""
📱 Interface Layout:
   ┌─────────────────┐ ┌─────────────────┐
   │ Dexter    [ON]  │ │ Analyst   [OFF] │
   │ Chat | Config   │ │ Chat | Config   │
   └─────────────────┘ └─────────────────┘
   
   ┌──────────┐ ┌──────────┐ ┌──────────┐
   │ Engineer │ │Research. │ │Special.  │
   │   [OFF]  │ │   [OFF]  │ │   [OFF]  │
   └──────────┘ └──────────┘ └──────────┘

🔧 Key Features:
   • 5 LLM panels (Dexter always first)
   • Real-time chat with conversation history
   • Editable configuration per panel
   • Enable/disable toggles for each LLM
   • Local-only operation (no server required)
   • Skills folder integration
   • Configuration persistence to config.json
""")
    
    print_step(3, "How to Use")
    print("""
🚀 Starting the CLI:
   python3 cli_ui_simple.py

⌨️  Key Bindings:
   • Q or Ctrl+C: Quit
   • F1: Show help
   • F5: Refresh config
   • Tab: Navigate elements
   • Enter: Send messages

🔧 Configuration:
   1. Click Config tab in any panel
   2. Set Provider (openai, ollama, anthropic, etc.)
   3. Set Model name and endpoint
   4. Set API key environment variable
   5. Configure identity, role, and prompts
   6. Click Save Configuration
   7. Toggle the switch to enable the LLM

💬 Chatting:
   1. Enable an LLM panel
   2. Go to Chat tab
   3. Type your message
   4. Press Enter or click Send
   5. View response in chat history
""")
    
    print_step(4, "Example Configurations")
    print("""
OpenAI GPT-4:
   Provider: openai
   Model: gpt-4o-mini
   Endpoint: https://api.openai.com/v1
   API Key Env: OPENAI_API_KEY

Local Ollama:
   Provider: ollama
   Model: llama3.1:8b
   Endpoint: http://localhost:11434
   API Key Env: (leave empty)

Anthropic Claude:
   Provider: anthropic
   Model: claude-3-sonnet-20240229
   Endpoint: https://api.anthropic.com/v1
   API Key Env: ANTHROPIC_API_KEY
""")
    
    print_step(5, "Environment Setup")
    print("""
Set your API keys as environment variables:

export OPENAI_API_KEY="your-openai-key"
export ANTHROPIC_API_KEY="your-anthropic-key"
export NEMOTRON_API_KEY="your-nemotron-key"

For local Ollama, ensure the server is running:
ollama serve
""")
    
    print_step(6, "Ready to Launch!")
    print("\n🎯 Run the CLI interface now:")
    print("   python3 cli_ui_simple.py")
    print("\n📚 For detailed documentation, see:")
    print("   CLI_README.md")
    
    # Optionally run the CLI
    print("\n" + "=" * 60)
    response = input("Would you like to launch the CLI now? (y/n): ").lower().strip()
    if response in ['y', 'yes']:
        print("\n🚀 Launching Gliksbot CLI...")
        try:
            subprocess.run([sys.executable, "cli_ui_simple.py"])
        except KeyboardInterrupt:
            print("\n👋 CLI session ended")
        except Exception as e:
            print(f"\n❌ Error launching CLI: {e}")
    else:
        print("\n👋 Demo complete! Launch the CLI anytime with: python3 cli_ui_simple.py")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())