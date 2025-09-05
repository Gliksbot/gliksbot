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

OPENAI_COMPAT_PROVIDERS = {"openai", "vultr", "nvidia", "custom"}

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
    if provider in OPENAI_COMPAT_PROVIDERS:
        return await _call_openai_compatible(model_config, prompt)
    elif provider == 'ollama':
        return await _call_ollama(model_config, prompt)
    elif provider == 'nemotron':
        return await _call_nemotron(model_config, prompt)
    elif provider == 'anthropic':
        return await _call_anthropic(model_config, prompt)
    else:
        raise ValueError(f"Unknown provider '{provider}' for LLM '{llm_name}'")

async def _call_openai_compatible(model_config: Dict[str, Any], prompt: str) -> str:
    """Call OpenAI compatible endpoint honoring configured endpoint URL."""
    api_key = model_config.get('api_key')
    if not api_key:
        raise ValueError("API key not configured")
    endpoint = (model_config.get('endpoint') or 'https://api.openai.com/v1').rstrip('/')
    url = f"{endpoint}/chat/completions"
    model = model_config.get('model', '')
    if not model:
        raise ValueError("Model not specified")
    params = model_config.get('params', {})
    identity = model_config.get('identity', '')
    role = model_config.get('role', '')
    system_prompt = f"{identity} {role}".strip()
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, headers=headers, json={
            "model": model,
            "messages": messages,
            "temperature": params.get('temperature', 0.7),
            "max_tokens": params.get('max_tokens', 2000)
        }, timeout=60.0)
        try:
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise ValueError(f"OpenAI-compatible API error {e.response.status_code}: {e.response.text}")
        data = resp.json()
        try:
            return data['choices'][0]['message']['content']
        except Exception:
            raise ValueError(f"Unexpected response format: {data}")

async def _call_anthropic(model_config: Dict[str, Any], prompt: str) -> str:
    """Minimal Anthropic messages API call (Claude)."""
    api_key = model_config.get('api_key')
    if not api_key:
        raise ValueError("Anthropic API key not configured")
    endpoint = (model_config.get('endpoint') or 'https://api.anthropic.com/v1').rstrip('/')
    url = f"{endpoint}/messages"
    model = model_config.get('model', '')
    identity = model_config.get('identity', '')
    role = model_config.get('role', '')
    system_prompt = f"{identity} {role}".strip()
    # Anthropic uses top-level system plus messages array with user roles
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    messages = [{"role": "user", "content": prompt}]
    body = {"model": model, "messages": messages, "max_tokens": model_config.get('params', {}).get('max_tokens', 1024)}
    if system_prompt:
        body["system"] = system_prompt
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, headers=headers, json=body, timeout=60.0)
        try:
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise ValueError(f"Anthropic API error {e.response.status_code}: {e.response.text}")
        data = resp.json()
        try:
            return ''.join(block.get('text', '') for block in data.get('content', [])) or str(data)
        except Exception:
            return str(data)

async def _call_ollama(model_config: Dict[str, Any], prompt: str) -> str:
    """Call Ollama API (local or remote)."""
    endpoint = model_config.get('endpoint', 'http://localhost:11434')
    model = model_config.get('model', 'llama3.1:8b-instruct-q4_0')
    params = model_config.get('params', {})
    
    # Validate model configuration
    if not model or model.strip() == "":
        raise ValueError(f"No model specified for Ollama. Please set the 'model' field in configuration.")
    
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
    
    try:
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
                        raise ValueError(f"Remote Ollama HTTP error {e.response.status_code}: {e.response.text}")
                except httpx.ConnectError as e:
                    raise ValueError(f"Failed to connect to remote Ollama at {endpoint}. Please check the endpoint URL. Error: {str(e)}")
                except httpx.TimeoutException as e:
                    raise ValueError(f"Remote Ollama request timed out after 120 seconds. Error: {str(e)}")
                except json.JSONDecodeError as e:
                    raise ValueError(f"Invalid response from remote Ollama server.")
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
    
    except httpx.ConnectError as e:
        raise ValueError(f"Failed to connect to Ollama at {endpoint}. Please ensure Ollama is running and accessible. Error: {str(e)}")
    except httpx.TimeoutException as e:
        raise ValueError(f"Ollama request timed out after 120 seconds. The model '{model}' may be loading for the first time. Error: {str(e)}")
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise ValueError(f"Model '{model}' not found in Ollama. Please run 'ollama pull {model}' to download it.")
        elif e.response.status_code == 500:
            raise ValueError(f"Ollama server error. The model '{model}' may not be compatible or loaded properly.")
        else:
            raise ValueError(f"Ollama HTTP error {e.response.status_code}: {e.response.text}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid response from Ollama server. Server may be starting up or misconfigured.")
    except Exception as e:
        raise ValueError(f"Unexpected error calling Ollama: {str(e)}")

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
    from .config import Config
    from .utils import get_config_path
    
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