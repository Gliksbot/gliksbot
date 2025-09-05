#!/usr/bin/env python3
"""
Gliksbot CLI-based Local UI with 5 LLM Panels

A simplified, local-first CLI user interface for Gliksbot featuring five equally
distributed panels for LLM slots. Eliminates the need for FastAPI/server by 
operating entirely locally with editable configurations and chat functionality.
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, Container
from textual.widgets import (
    Header, Footer, TextArea, Input, Button, Label, 
    Switch, Static, Tabs, TabbedContent, TabPane
)
from textual.reactive import reactive
from textual import events
from textual.binding import Binding

# Add the backend directory to path for imports
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_path)

# Direct imports to avoid FastAPI dependencies
from dexter_brain.config import Config
from dexter_brain.llm import call_slot
from dexter_brain.utils import get_config_path


class LLMPanel(Container):
    """Individual LLM panel with chat and configuration capabilities."""
    
    def __init__(self, slot_name: str, slot_config: Dict[str, Any], **kwargs):
        super().__init__(**kwargs)
        self.slot_name = slot_name
        self.slot_config = slot_config.copy()
        self.chat_history = []
        self.is_dexter = slot_name == "dexter"
        
    def compose(self) -> ComposeResult:
        """Create the panel UI components."""
        with Vertical():
            # Panel header with title and status
            with Horizontal(classes="panel-header"):
                yield Label(f"[bold]{self.slot_name.title()}[/bold]", classes="panel-title")
                yield Switch(
                    value=self.slot_config.get('enabled', False),
                    id=f"switch-{self.slot_name}",
                    classes="panel-switch"
                )
            
            # Tabbed content for Chat and Config
            with TabbedContent():
                with TabPane("Chat", id=f"chat-{self.slot_name}"):
                    yield TextArea(
                        text="",
                        read_only=True,
                        id=f"chat-display-{self.slot_name}",
                        classes="chat-display"
                    )
                    with Horizontal(classes="chat-input-row"):
                        yield Input(
                            placeholder="Type your message...",
                            id=f"chat-input-{self.slot_name}",
                            classes="chat-input"
                        )
                        yield Button(
                            "Send",
                            id=f"send-{self.slot_name}",
                            classes="send-button"
                        )
                
                with TabPane("Config", id=f"config-{self.slot_name}"):
                    yield self._create_config_form()
    
    def _create_config_form(self) -> Container:
        """Create the configuration form for this LLM slot."""
        with Vertical(classes="config-form"):
            # Provider selection
            yield Label("Provider:")
            yield Input(
                value=self.slot_config.get('provider', ''),
                placeholder="e.g., openai, ollama, anthropic",
                id=f"config-provider-{self.slot_name}"
            )
            
            # Model name
            yield Label("Model:")
            yield Input(
                value=self.slot_config.get('model', ''),
                placeholder="e.g., gpt-4, llama3.1:8b",
                id=f"config-model-{self.slot_name}"
            )
            
            # Endpoint URL
            yield Label("Endpoint:")
            yield Input(
                value=self.slot_config.get('endpoint', ''),
                placeholder="e.g., https://api.openai.com/v1",
                id=f"config-endpoint-{self.slot_name}"
            )
            
            # API Key Environment Variable
            yield Label("API Key Environment Variable:")
            yield Input(
                value=self.slot_config.get('api_key_env', ''),
                placeholder="e.g., OPENAI_API_KEY",
                id=f"config-api-key-env-{self.slot_name}"
            )
            
            # Identity/Role
            yield Label("Identity:")
            yield TextArea(
                text=self.slot_config.get('identity', ''),
                id=f"config-identity-{self.slot_name}",
                classes="config-textarea"
            )
            
            # Role
            yield Label("Role:")
            yield Input(
                value=self.slot_config.get('role', ''),
                placeholder="e.g., Senior Software Engineer",
                id=f"config-role-{self.slot_name}"
            )
            
            # System Prompt
            yield Label("System Prompt:")
            yield TextArea(
                text=self.slot_config.get('prompt', ''),
                id=f"config-prompt-{self.slot_name}",
                classes="config-textarea"
            )
            
            # Save button
            yield Button(
                "Save Configuration",
                id=f"save-config-{self.slot_name}",
                classes="save-button"
            )
            
            # Status display
            yield Label(
                "Ready" if self.slot_config.get('enabled') else "Disabled",
                id=f"status-{self.slot_name}",
                classes="status-label"
            )
    
    async def send_message(self, message: str, config: Config) -> str:
        """Send a message to this LLM and return the response."""
        try:
            # Add user message to history
            self.chat_history.append(f"User: {message}")
            
            # Call the LLM
            response = await call_slot(config, self.slot_name, message)
            
            # Add response to history
            self.chat_history.append(f"{self.slot_name.title()}: {response}")
            
            return response
            
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            self.chat_history.append(error_msg)
            return error_msg
    
    def update_chat_display(self):
        """Update the chat display with current history."""
        chat_display = self.query_one(f"#chat-display-{self.slot_name}", TextArea)
        chat_text = "\n\n".join(self.chat_history)
        chat_display.text = chat_text
        # Scroll to bottom
        chat_display.scroll_end(animate=False)
    
    def get_config_values(self) -> Dict[str, Any]:
        """Get current configuration values from the form."""
        config = {}
        try:
            config['provider'] = self.query_one(f"#config-provider-{self.slot_name}", Input).value
            config['model'] = self.query_one(f"#config-model-{self.slot_name}", Input).value
            config['endpoint'] = self.query_one(f"#config-endpoint-{self.slot_name}", Input).value
            config['api_key_env'] = self.query_one(f"#config-api-key-env-{self.slot_name}", Input).value
            config['identity'] = self.query_one(f"#config-identity-{self.slot_name}", TextArea).text
            config['role'] = self.query_one(f"#config-role-{self.slot_name}", Input).value
            config['prompt'] = self.query_one(f"#config-prompt-{self.slot_name}", TextArea).text
            config['enabled'] = self.query_one(f"#switch-{self.slot_name}", Switch).value
        except Exception as e:
            self.app.log(f"Error getting config values for {self.slot_name}: {e}")
        return config
    
    def update_status(self, message: str):
        """Update the status label."""
        try:
            status_label = self.query_one(f"#status-{self.slot_name}", Label)
            status_label.update(message)
        except Exception:
            pass


class GliksbotCLI(App):
    """Main CLI application for Gliksbot with 5 LLM panels."""
    
    TITLE = "Gliksbot CLI - Local Multi-LLM Interface"
    CSS_PATH = "cli_ui.tcss"
    
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("ctrl+c", "quit", "Quit"),
        Binding("f1", "help", "Help"),
        Binding("f5", "refresh", "Refresh"),
    ]
    
    def __init__(self):
        super().__init__()
        self.config = None
        self.config_path = None
        self.panels = {}
        # Default 5 LLM slots - Dexter is always first
        self.slot_names = ["dexter", "analyst", "engineer", "researcher", "specialist"]
        self.load_config()
    
    def load_config(self):
        """Load the main configuration file."""
        try:
            self.config_path = get_config_path()
            self.config = Config.load(self.config_path)
            self.log(f"Configuration loaded from {self.config_path}")
        except Exception as e:
            self.log(f"Error loading config: {e}")
            # Create minimal config if none exists
            self.config = self._create_minimal_config()
    
    def _create_minimal_config(self):
        """Create a minimal configuration for testing."""
        minimal_data = {
            "models": {
                "dexter": {
                    "enabled": True,
                    "provider": "ollama",
                    "model": "llama3.1:8b",
                    "endpoint": "http://localhost:11434",
                    "identity": "You are Dexter, the orchestrator",
                    "role": "Chief Orchestrator",
                    "prompt": "You coordinate multi-LLM teams."
                }
            }
        }
        # Add empty configs for other slots
        for slot in self.slot_names[1:]:
            minimal_data["models"][slot] = {
                "enabled": False,
                "provider": "",
                "model": "",
                "identity": f"You are the {slot} specialist",
                "role": f"{slot.title()} Specialist"
            }
        
        return Config(minimal_data)
    
    def compose(self) -> ComposeResult:
        """Create the main UI layout."""
        yield Header()
        
        # Create 5-panel layout (2 top, 3 bottom for better space usage)
        with Vertical():
            # Top row - 2 panels
            with Horizontal(classes="panel-row"):
                for slot_name in self.slot_names[:2]:
                    slot_config = self.config.models.get(slot_name, {})
                    panel = LLMPanel(slot_name, slot_config, classes="llm-panel")
                    self.panels[slot_name] = panel
                    yield panel
            
            # Bottom row - 3 panels  
            with Horizontal(classes="panel-row"):
                for slot_name in self.slot_names[2:]:
                    slot_config = self.config.models.get(slot_name, {})
                    panel = LLMPanel(slot_name, slot_config, classes="llm-panel")
                    self.panels[slot_name] = panel
                    yield panel
        
        yield Footer()
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id
        
        if button_id.startswith("send-"):
            # Send message button
            slot_name = button_id.replace("send-", "")
            await self._handle_send_message(slot_name)
        
        elif button_id.startswith("save-config-"):
            # Save configuration button
            slot_name = button_id.replace("save-config-", "")
            await self._handle_save_config(slot_name)
    
    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle Enter key in chat input."""
        input_id = event.input.id
        if input_id.startswith("chat-input-"):
            slot_name = input_id.replace("chat-input-", "")
            await self._handle_send_message(slot_name)
    
    async def _handle_send_message(self, slot_name: str):
        """Handle sending a message to an LLM."""
        try:
            # Get the message from input
            chat_input = self.query_one(f"#chat-input-{slot_name}", Input)
            message = chat_input.value.strip()
            
            if not message:
                return
            
            # Clear the input
            chat_input.value = ""
            
            # Check if the LLM is enabled
            panel = self.panels[slot_name]
            if not panel.slot_config.get('enabled', False):
                panel.chat_history.append(f"Error: {slot_name} is not enabled")
                panel.update_chat_display()
                return
            
            # Update status to show processing
            panel.update_status("Processing...")
            
            # Send message to LLM
            response = await panel.send_message(message, self.config)
            
            # Update chat display
            panel.update_chat_display()
            
            # Update status
            panel.update_status("Ready")
            
        except Exception as e:
            self.log(f"Error sending message to {slot_name}: {e}")
            panel = self.panels[slot_name]
            panel.chat_history.append(f"Error: {str(e)}")
            panel.update_chat_display()
            panel.update_status("Error")
    
    async def _handle_save_config(self, slot_name: str):
        """Handle saving configuration for an LLM slot."""
        try:
            panel = self.panels[slot_name]
            new_config = panel.get_config_values()
            
            # Update the panel's config
            panel.slot_config.update(new_config)
            
            # Update the main config
            if slot_name not in self.config.models:
                self.config.models[slot_name] = {}
            self.config.models[slot_name].update(new_config)
            
            # Save to file
            await self._save_config_to_file()
            
            # Update status
            panel.update_status("Configuration saved")
            
            self.log(f"Configuration saved for {slot_name}")
            
        except Exception as e:
            self.log(f"Error saving config for {slot_name}: {e}")
            panel = self.panels[slot_name]
            panel.update_status(f"Save failed: {str(e)}")
    
    async def _save_config_to_file(self):
        """Save the current configuration to file."""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config.to_json(), f, indent=2)
        except Exception as e:
            self.log(f"Error saving config file: {e}")
            raise
    
    def action_help(self) -> None:
        """Show help information."""
        help_text = """
Gliksbot CLI Help:

Key Bindings:
- F1: Show this help
- F5: Refresh configuration
- Q or Ctrl+C: Quit

Panel Features:
- Chat Tab: Send messages to LLMs
- Config Tab: Edit LLM configurations
- Switch: Enable/disable each LLM slot

LLM Slots:
1. Dexter (always first) - Main orchestrator
2. Analyst - Data analysis specialist  
3. Engineer - Software development specialist
4. Researcher - Research specialist
5. Specialist - Configurable domain expert

Configuration:
- All settings are saved locally to config.json
- API keys should be set as environment variables
- Each slot can be independently configured and enabled
        """
        self.push_screen("help", lambda: self.app.mount(Static(help_text)))
    
    def action_refresh(self) -> None:
        """Reload configuration from file."""
        try:
            self.load_config()
            # TODO: Update all panels with new config
            self.log("Configuration refreshed")
        except Exception as e:
            self.log(f"Error refreshing config: {e}")


def main():
    """Main entry point for the CLI application."""
    app = GliksbotCLI()
    app.run()


if __name__ == "__main__":
    main()