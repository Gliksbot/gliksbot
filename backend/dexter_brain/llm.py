"""
LLM provider implementations for Dexter v3.
Handles communication with different LLM providers including OpenAI, Ollama, and Nemotron.
"""

from __future__ import annotations
import asyncio
import json
import os
from typing import Any, Dict, Optional
import httpx

async def call_slot(config, llm_name: str, prompt: str) -> str:
    """
    Call a specific LLM slot with the given prompt.
    
    Args:
        config: Configuration object containing LLM settings
        llm_name: Name of the LLM to call (e.g., 'openai', 'ollama', 'nemotron')
        prompt: The prompt to send to the LLM
        
    Returns:
        The LLM's response as a string
    """
    models = config.models
    if llm_name not in models:
        raise ValueError(f"LLM '{llm_name}' not found in configuration")
    
    model_config = models[llm_name]
    if not model_config.get('enabled', False):
        raise ValueError(f"LLM '{llm_name}' is not enabled")
    
    provider = model_config.get('provider', '').lower()
    
    if provider == 'openai':
        return await _call_openai(model_config, prompt)
    elif provider == 'ollama':
        return await _call_ollama(model_config, prompt)
    elif provider == 'nemotron':
        return await _call_nemotron(model_config, prompt)
    elif provider == 'vultr':
        # Vultr uses OpenAI-compatible API format
        return await _call_openai(model_config, prompt)
    elif provider == 'anthropic':
        # Anthropic has different API format - for now use OpenAI format as fallback
        return await _call_openai(model_config, prompt)
    elif provider == 'nvidia':
        # NVIDIA uses OpenAI-compatible API format
        return await _call_openai(model_config, prompt)
    elif provider == 'custom':
        # Custom API endpoint - assume OpenAI-compatible format
        return await _call_openai(model_config, prompt)
    else:
        raise ValueError(f"Unknown provider '{provider}' for LLM '{llm_name}'")

async def _call_openai(model_config: Dict[str, Any], prompt: str) -> str:
    """Call OpenAI API."""
    api_key = model_config.get('api_key')
    if not api_key:
        raise ValueError("OpenAI API key not configured")
    
    model = model_config.get('model', 'gpt-4o-mini')
    params = model_config.get('params', {})
    
    # Add identity and role to the prompt
    identity = model_config.get('identity', '')
    role = model_config.get('role', '')
    system_prompt = f"{identity} {role}".strip()
    
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": model,
                "messages": messages,
                "temperature": params.get('temperature', 0.7),
                "max_tokens": params.get('max_tokens', 2000)
            },
            timeout=60.0
        )
        response.raise_for_status()
        data = response.json()
        return data['choices'][0]['message']['content']

async def _call_ollama(model_config: Dict[str, Any], prompt: str) -> str:
    """Call Ollama API (local or remote)."""
    endpoint = model_config.get('endpoint', 'http://localhost:11434')
    model = model_config.get('model', 'llama3.1:8b-instruct-q4_0')
    params = model_config.get('params', {})
    
    # Get API key if needed for remote Ollama service
    api_key = None
    api_key_env = model_config.get('api_key_env')
    if api_key_env:
        api_key = os.environ.get(api_key_env)
    
    # Add identity and role to the prompt
    identity = model_config.get('identity', '')
    role = model_config.get('role', '')
    system_prompt = f"{identity} {role}".strip()
    
    # Check if this is a remote Ollama service (has API key and https endpoint)
    is_remote = api_key and endpoint.startswith('https')
    
    async with httpx.AsyncClient() as client:
        if is_remote:
            # Use chat format for remote Ollama service - try the correct endpoint
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            # Try the direct chat endpoint first
            try:
                response = await client.post(
                    f"{endpoint}/api/chat",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": model,
                        "messages": messages,
                        "stream": False,
                        "options": {
                            "temperature": params.get('temperature', 0.2),
                            "num_ctx": params.get('num_ctx', 4096)
                        }
                    },
                    timeout=120.0
                )
                response.raise_for_status()
                data = response.json()
                return data['message']['content']
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    # Fall back to generate endpoint for remote Ollama
                    full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
                    
                    response = await client.post(
                        f"{endpoint}/api/generate",
                        headers={
                            "Authorization": f"Bearer {api_key}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "model": model,
                            "prompt": full_prompt,
                            "stream": False,
                            "options": {
                                "temperature": params.get('temperature', 0.2),
                                "top_p": params.get('top_p', 0.9),
                                "num_ctx": params.get('num_ctx', 4096)
                            }
                        },
                        timeout=120.0
                    )
                    response.raise_for_status()
                    data = response.json()
                    return data['response']
                else:
                    raise
        else:
            # Use generate format for local Ollama
            full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
            
            # Prepare headers
            headers = {"Content-Type": "application/json"}
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"
            
            response = await client.post(
                f"{endpoint}/api/generate",
                headers=headers,
                json={
                    "model": model,
                    "prompt": full_prompt,
                    "stream": False,
                    "options": {
                        "temperature": params.get('temperature', 0.2),
                        "top_p": params.get('top_p', 0.9),
                        "num_ctx": params.get('num_ctx', 4096)
                    }
                },
                timeout=120.0
            )
            response.raise_for_status()
            data = response.json()
            return data['response']

async def _call_nemotron(model_config: Dict[str, Any], prompt: str) -> str:
    """Call Nemotron API."""
    api_key = model_config.get('api_key')
    if not api_key:
        raise ValueError("Nemotron API key not configured")
    
    endpoint = model_config.get('endpoint', 'https://api.nemotron.ai')
    model = model_config.get('model', 'nemotron-340b-instruct')
    params = model_config.get('params', {})
    
    # Add identity and role to the prompt
    identity = model_config.get('identity', '')
    role = model_config.get('role', '')
    system_prompt = f"{identity} {role}".strip()
    
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{endpoint}/api/chat",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": model,
                "messages": messages,
                "stream": False
            },
            timeout=60.0
        )
        response.raise_for_status()
        data = response.json()
        return data['message']['content']

# Test function for development
async def test_llm_call():
    """Test function for development."""
    from dexter_brain.config import Config
    from dexter_brain.utils import get_config_path
    
    config = Config.load(get_config_path())
    
    # Test with enabled LLMs
    for llm_name, model_config in config.models.items():
        if model_config.get('enabled'):
            try:
                response = await call_slot(config, llm_name, "Hello, please respond with a brief test message.")
                print(f"{llm_name}: {response[:100]}...")
            except Exception as e:
                print(f"{llm_name}: Error - {e}")

if __name__ == "__main__":
    asyncio.run(test_llm_call())